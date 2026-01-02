"""
Quick test script for DuckDB setup
Run with: python test_duckdb.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emp54_django.settings')
django.setup()

from services.duckdb_client import duckdb_client
import duckdb

print("=" * 60)
print("DuckDB Setup Test")
print("=" * 60)

# Test 1: Basic DuckDB functionality
print("\n[Test 1] DuckDB installed and working")
try:
    conn = duckdb.connect(':memory:')
    result = conn.execute("SELECT 'Hello DuckDB!' as message").fetchone()
    print(f"  Result: {result[0]}")
    conn.close()
    print("  PASS")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 2: DuckDB client configuration
print("\n[Test 2] DuckDB client configuration")
try:
    print(f"  Wasabi Endpoint: {duckdb_client.wasabi_endpoint}")
    print(f"  Wasabi Region: {duckdb_client.wasabi_region}")
    print(f"  Wasabi Bucket: {duckdb_client.wasabi_bucket}")
    print(f"  Access Key configured: {'Yes' if duckdb_client.wasabi_access_key else 'No'}")
    print(f"  Secret Key configured: {'Yes' if duckdb_client.wasabi_secret_key else 'No'}")
    print("  PASS")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 3: Create connection with S3 support
print("\n[Test 3] DuckDB connection with S3/Wasabi support")
try:
    conn = duckdb_client.get_connection()

    # Test httpfs extension
    result = conn.execute("SELECT * FROM duckdb_extensions() WHERE extension_name = 'httpfs'").fetchone()
    if result:
        print(f"  httpfs extension: {result[1]} (loaded: {result[2]})")

    # Test S3 configuration
    endpoint = conn.execute("SELECT current_setting('s3_endpoint')").fetchone()
    region = conn.execute("SELECT current_setting('s3_region')").fetchone()
    print(f"  S3 Endpoint: {endpoint[0]}")
    print(f"  S3 Region: {region[0]}")

    conn.close()
    print("  PASS")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Test 4: Create sample Parquet file and query it
print("\n[Test 4] Create and query Parquet file")
try:
    import pandas as pd
    import pyarrow.parquet as pq
    import pyarrow as pa

    # Create sample data
    df = pd.DataFrame({
        'vendor': ['Acme Corp', 'Best Buy', 'Costco', 'Dell Inc'],
        'amount': [1500.00, 2300.50, 1800.75, 3200.00],
        'order_count': [10, 15, 12, 20]
    })

    # Write to Parquet
    test_file = 'test_sample.parquet'
    table = pa.Table.from_pandas(df)
    pq.write_table(table, test_file, compression='snappy')
    print(f"  Created {test_file} ({os.path.getsize(test_file)} bytes)")

    # Query with DuckDB
    results = duckdb_client.query(f"""
        SELECT vendor, amount, order_count
        FROM '{test_file}'
        WHERE amount > 2000
        ORDER BY amount DESC
    """)

    print(f"  Query results ({len(results)} rows):")
    for row in results:
        print(f"    - {row['vendor']}: ${row['amount']:,.2f} ({row['order_count']} orders)")

    # Cleanup
    os.remove(test_file)
    print("  PASS")
except Exception as e:
    print(f"  FAIL: {e}")
    if os.path.exists('test_sample.parquet'):
        os.remove('test_sample.parquet')
    sys.exit(1)

# Test 5: Test MongoDB connection (for export)
print("\n[Test 5] MongoDB connection (for export)")
try:
    from pymongo import MongoClient
    from decouple import config

    mongo_uri = config('MONGODB_URI')
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

    # Test connection
    client.admin.command('ping')

    # Get database info
    db_name = config('MONGODB_DATABASE', default='emp54')
    db = client[db_name]

    # Check for purchase_orders collection
    collections = db.list_collection_names()
    print(f"  Database: {db_name}")
    print(f"  Collections found: {len(collections)}")

    if 'purchase_orders' in collections:
        count = db.purchase_orders.count_documents({})
        print(f"  purchase_orders collection: {count:,} records")
    else:
        print(f"  WARNING: purchase_orders collection not found")
        print(f"  Available collections: {', '.join(collections[:5])}")

    client.close()
    print("  PASS")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("SUCCESS! All tests passed! DuckDB is ready to rock!")
print("=" * 60)
print("\nNext steps:")
print("1. Run: python manage.py shell")
print("2. Import: from scripts.migrate_mongodb_to_parquet import export_collection_to_parquet")
print("3. Export: export_collection_to_parquet('purchase_orders', 'purchase_orders.parquet')")
