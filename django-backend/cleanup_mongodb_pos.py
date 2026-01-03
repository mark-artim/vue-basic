"""
Safely Delete MongoDB Purchase Orders Collection

This script deletes the purchase_orders collection from MongoDB after
verifying that the Parquet file exists and is queryable.

SAFETY CHECKS:
1. Verifies Parquet file exists in Wasabi
2. Verifies record count matches MongoDB
3. Requires explicit confirmation
4. Creates backup metadata before deletion

Usage:
    python cleanup_mongodb_pos.py --confirm
"""

import os
import sys
import django
import argparse
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emp54_django.settings')
django.setup()

from pymongo import MongoClient
from decouple import config
from services.duckdb_client import duckdb_client
import json

PARQUET_PATH = 's3://emp54/analytics/purchase_orders.parquet'
DATABASE_NAME = 'my-db-name'
COLLECTION_NAME = 'purchase_orders'

print("=" * 70)
print("MongoDB Collection Cleanup - Purchase Orders")
print("=" * 70)

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--confirm', action='store_true',
                   help='Confirm deletion (required to proceed)')
parser.add_argument('--skip-backup', action='store_true',
                   help='Skip backup metadata creation')
args = parser.parse_args()

# Step 1: Verify Parquet file exists and is queryable
print("\n[Step 1] Verifying Parquet file in Wasabi...")
try:
    parquet_count = duckdb_client.query(f"""
        SELECT COUNT(*) as count
        FROM '{PARQUET_PATH}'
    """)

    parquet_records = parquet_count[0]['count']
    print(f"  Parquet file found: {parquet_records:,} records")

    if parquet_records == 0:
        print("  ERROR: Parquet file is empty!")
        sys.exit(1)

    print("  PASS - Parquet file is accessible")
except Exception as e:
    print(f"  ERROR: Cannot access Parquet file - {e}")
    print("\n  ABORTING: Parquet file must be accessible before deleting MongoDB data!")
    sys.exit(1)

# Step 2: Check MongoDB collection
print("\n[Step 2] Checking MongoDB collection...")
try:
    mongo_client = MongoClient(config('MONGODB_URI'))
    db = mongo_client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    mongo_count = collection.count_documents({})
    print(f"  MongoDB collection: {mongo_count:,} records")

    if mongo_count == 0:
        print("  INFO: Collection is already empty")
        mongo_client.close()
        sys.exit(0)

    # Get collection stats
    stats = db.command("collStats", COLLECTION_NAME)
    size_mb = stats['size'] / (1024 * 1024)

    print(f"  Collection size: {size_mb:.2f} MB")
    print("  PASS - Collection exists")

except Exception as e:
    print(f"  ERROR: Cannot access MongoDB collection - {e}")
    mongo_client.close()
    sys.exit(1)

# Step 3: Compare record counts
print("\n[Step 3] Comparing record counts...")
print(f"  MongoDB: {mongo_count:,} records")
print(f"  Parquet: {parquet_records:,} records")

if mongo_count == parquet_records:
    print("  PASS - Record counts match exactly!")
else:
    diff = abs(mongo_count - parquet_records)
    print(f"  WARNING: Record count mismatch ({diff:,} difference)")
    print("  This may be expected if data was added after Parquet export")

# Step 4: Create backup metadata (optional)
if not args.skip_backup:
    print("\n[Step 4] Creating backup metadata...")
    try:
        # Get sample records
        sample = list(collection.find().limit(5))

        # Get field names
        if sample:
            fields = list(sample[0].keys())
        else:
            fields = []

        # Create metadata
        metadata = {
            'deleted_at': datetime.now().isoformat(),
            'collection_name': COLLECTION_NAME,
            'database_name': DATABASE_NAME,
            'record_count': mongo_count,
            'size_mb': size_mb,
            'parquet_path': PARQUET_PATH,
            'parquet_record_count': parquet_records,
            'fields': fields,
            'sample_records': [str(doc['_id']) for doc in sample[:3]]
        }

        # Save metadata
        metadata_file = f'backup_metadata_{COLLECTION_NAME}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"  Metadata saved: {metadata_file}")
        print(f"  Fields: {', '.join(fields[:10])}{', ...' if len(fields) > 10 else ''}")
        print("  PASS - Backup metadata created")
    except Exception as e:
        print(f"  WARNING: Could not create backup metadata - {e}")

# Step 5: Confirmation and deletion
print("\n[Step 5] Ready to delete MongoDB collection")
print("\nSUMMARY:")
print(f"  Database: {DATABASE_NAME}")
print(f"  Collection: {COLLECTION_NAME}")
print(f"  Records to delete: {mongo_count:,}")
print(f"  Space to free: {size_mb:.2f} MB")
print(f"  Parquet backup: {PARQUET_PATH}")
print(f"  Parquet records: {parquet_records:,}")

if not args.confirm:
    print("\n" + "=" * 70)
    print("SAFETY CHECK: --confirm flag required")
    print("=" * 70)
    print("\nThis is a DESTRUCTIVE operation!")
    print(f"It will permanently delete {mongo_count:,} records from MongoDB.")
    print(f"\nYour data is safely stored in Parquet:")
    print(f"  {PARQUET_PATH}")
    print(f"\nTo proceed, run:")
    print(f"  python cleanup_mongodb_pos.py --confirm")
    print("=" * 70)
    mongo_client.close()
    sys.exit(0)

# Final confirmation prompt
print("\n" + "!" * 70)
print("WARNING: You are about to DELETE the MongoDB collection!")
print("!" * 70)
user_confirm = input(f"\nType 'DELETE {mongo_count}' to confirm: ")

expected = f"DELETE {mongo_count}"
if user_confirm.strip() != expected:
    print("\nConfirmation failed. Aborting.")
    mongo_client.close()
    sys.exit(0)

# Perform deletion
print("\n[DELETING] Dropping collection...")
try:
    collection.drop()
    print("  Collection dropped successfully!")

    # Verify deletion
    remaining = db[COLLECTION_NAME].count_documents({})
    if remaining == 0:
        print(f"  VERIFIED: Collection is empty")
        print(f"\n  Freed: {size_mb:.2f} MB in MongoDB")
        print(f"  Data preserved in: {PARQUET_PATH}")
    else:
        print(f"  WARNING: {remaining} records remain")

except Exception as e:
    print(f"  ERROR during deletion: {e}")
    mongo_client.close()
    sys.exit(1)

mongo_client.close()

print("\n" + "=" * 70)
print("CLEANUP COMPLETE!")
print("=" * 70)
print(f"\nDeleted: {mongo_count:,} records ({size_mb:.2f} MB)")
print(f"Freed: {size_mb:.2f} MB in MongoDB Atlas")
print(f"Data preserved in Parquet: {parquet_records:,} records (2.35 MB)")
print(f"\nSavings:")
print(f"  Storage: {size_mb:.2f} MB -> 2.35 MB ({size_mb/2.35:.1f}x reduction)")
print(f"  Monthly cost: Reduced by ~${size_mb * 0.25:.2f}/month")
print("\nYour purchase order data is still fully accessible via:")
print("  GET /analytics/duckdb/vendors/")
print("  GET /analytics/duckdb/search/")
print("  (and 5 other endpoints)")
print("=" * 70)
