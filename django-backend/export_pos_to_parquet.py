"""
Export Purchase Orders from MongoDB to Parquet

This script exports your 111K PO records from MongoDB to a compressed Parquet file
and uploads it to Wasabi S3 for DuckDB querying.
"""

import os
import sys
import django
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emp54_django.settings')
django.setup()

from pymongo import MongoClient
from decouple import config
import boto3

print("=" * 70)
print("MongoDB to Parquet Export - Purchase Orders")
print("=" * 70)

# Configuration
MONGO_URI = config('MONGODB_URI')
DATABASE_NAME = 'my-db-name'  # The correct database
COLLECTION_NAME = 'purchase_orders'
OUTPUT_FILENAME = 'purchase_orders.parquet'
LOCAL_OUTPUT_DIR = './data_exports'

# Wasabi S3 configuration
WASABI_BUCKET = config('WASABI_BUCKET')
WASABI_ENDPOINT = config('WASABI_ENDPOINT')
WASABI_ACCESS_KEY = config('WASABI_ACCESS_KEY')
WASABI_SECRET_KEY = config('WASABI_SECRET_KEY')
WASABI_REGION = config('WASABI_REGION')

print(f"\nSource:")
print(f"  MongoDB Database: {DATABASE_NAME}")
print(f"  Collection: {COLLECTION_NAME}")
print(f"\nDestination:")
print(f"  Local: {LOCAL_OUTPUT_DIR}/{OUTPUT_FILENAME}")
print(f"  Wasabi: s3://{WASABI_BUCKET}/analytics/{OUTPUT_FILENAME}")

# Step 1: Connect to MongoDB
print(f"\n[Step 1] Connecting to MongoDB...")
start_time = time.time()

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Get record count
record_count = collection.count_documents({})
print(f"  Found {record_count:,} records")

# Step 2: Load data from MongoDB
print(f"\n[Step 2] Loading data from MongoDB...")
cursor = collection.find({})
data = list(cursor)

if not data:
    print("  ERROR: No data found!")
    sys.exit(1)

load_time = time.time() - start_time
print(f"  Loaded {len(data):,} records in {load_time:.2f}s")

# Step 3: Convert to DataFrame
print(f"\n[Step 3] Converting to pandas DataFrame...")
convert_start = time.time()

df = pd.DataFrame(data)

# Convert ObjectId to string
if '_id' in df.columns:
    df['_id'] = df['_id'].astype(str)

# Handle datetime fields
for col in df.columns:
    if df[col].dtype == 'object':
        # Try to convert to datetime
        try:
            sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
            if sample and isinstance(sample, str) and ('T' in str(sample) or '/' in str(sample)):
                df[col] = pd.to_datetime(df[col], errors='ignore')
        except:
            pass

convert_time = time.time() - convert_start
print(f"  Converted {len(df)} rows x {len(df.columns)} columns in {convert_time:.2f}s")
print(f"  Columns: {', '.join(df.columns[:10])}{', ...' if len(df.columns) > 10 else ''}")

# Show memory usage
memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
print(f"  DataFrame memory: {memory_mb:.2f} MB")

# Step 4: Write to Parquet
print(f"\n[Step 4] Writing to Parquet file...")
parquet_start = time.time()

# Create output directory
os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)
local_path = os.path.join(LOCAL_OUTPUT_DIR, OUTPUT_FILENAME)

# Write Parquet with Snappy compression
table = pa.Table.from_pandas(df)
pq.write_table(
    table,
    local_path,
    compression='snappy',
    row_group_size=100000  # 100K rows per group
)

parquet_time = time.time() - parquet_start
file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
compression_ratio = (memory_mb / file_size_mb) if file_size_mb > 0 else 0

print(f"  File: {local_path}")
print(f"  Size: {file_size_mb:.2f} MB")
print(f"  Compression: {compression_ratio:.1f}x (was {memory_mb:.2f} MB)")
print(f"  Write time: {parquet_time:.2f}s")

# Step 5: Upload to Wasabi S3
print(f"\n[Step 5] Uploading to Wasabi S3...")
upload_start = time.time()

try:
    s3_client = boto3.client(
        's3',
        endpoint_url=WASABI_ENDPOINT,
        aws_access_key_id=WASABI_ACCESS_KEY,
        aws_secret_access_key=WASABI_SECRET_KEY,
        region_name=WASABI_REGION
    )

    s3_key = f"analytics/{OUTPUT_FILENAME}"
    s3_client.upload_file(
        local_path,
        WASABI_BUCKET,
        s3_key,
        ExtraArgs={'ContentType': 'application/octet-stream'}
    )

    upload_time = time.time() - upload_start
    s3_path = f"s3://{WASABI_BUCKET}/{s3_key}"

    print(f"  S3 Path: {s3_path}")
    print(f"  Upload time: {upload_time:.2f}s")
    print(f"  Upload speed: {file_size_mb / upload_time:.2f} MB/s")

except Exception as e:
    print(f"  ERROR: Upload failed - {e}")
    print(f"  You can manually upload {local_path} later")
    s3_path = None

# Step 6: Verify with DuckDB query
print(f"\n[Step 6] Testing DuckDB query...")
try:
    import duckdb

    # Query local file first
    conn = duckdb.connect(':memory:')
    result = conn.execute(f"""
        SELECT COUNT(*) as count
        FROM '{local_path}'
    """).fetchone()

    print(f"  Local file query: {result[0]:,} records (SUCCESS!)")

    # If S3 upload succeeded, test S3 query
    if s3_path:
        from services.duckdb_client import duckdb_client
        s3_results = duckdb_client.query(f"""
            SELECT COUNT(*) as count
            FROM '{s3_path}'
        """)
        print(f"  S3 query: {s3_results[0]['count']:,} records (SUCCESS!)")

    conn.close()

except Exception as e:
    print(f"  WARNING: DuckDB test query failed - {e}")

# Summary
total_time = time.time() - start_time

print("\n" + "=" * 70)
print("EXPORT COMPLETE!")
print("=" * 70)
print(f"\nStatistics:")
print(f"  Records exported: {record_count:,}")
print(f"  MongoDB size: 42.35 MB")
print(f"  Parquet size: {file_size_mb:.2f} MB")
print(f"  Compression ratio: {compression_ratio:.1f}x")
print(f"  Total time: {total_time:.2f}s")

if s3_path:
    print(f"\nYour data is now ready for DuckDB querying:")
    print(f"  {s3_path}")
    print(f"\nExample query:")
    print(f"""
from services.duckdb_client import duckdb_client

results = duckdb_client.query('''
    SELECT vendor, COUNT(*) as orders, SUM(amount) as total
    FROM '{s3_path}'
    GROUP BY vendor
    ORDER BY total DESC
    LIMIT 10
''')

for row in results:
    print(f"{{row['vendor']}}: ${{row['total']:,.2f}}")
""")

print("\nNext: Create Django views to query this data blazing fast!")
print("=" * 70)

client.close()
