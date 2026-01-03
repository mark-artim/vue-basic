"""
Check MongoDB collections and record counts
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emp54_django.settings')
django.setup()

from pymongo import MongoClient
from decouple import config

mongo_uri = config('MONGODB_URI')
client = MongoClient(mongo_uri)

# Get database
db_name = config('MONGODB_DATABASE', default='emp54')
db = client[db_name]

print("=" * 60)
print(f"MongoDB Database: {db_name}")
print("=" * 60)

collections = db.list_collection_names()

if not collections:
    print("\nNo collections found in this database.")
    print("\nChecking all databases...")
    for db_name in client.list_database_names():
        if db_name not in ['admin', 'local', 'config']:
            print(f"\n  Database: {db_name}")
            temp_db = client[db_name]
            cols = temp_db.list_collection_names()
            for col in cols:
                count = temp_db[col].count_documents({})
                size_mb = temp_db.command("collStats", col)['size'] / (1024 * 1024)
                print(f"    - {col}: {count:,} records ({size_mb:.2f} MB)")
else:
    print(f"\n{len(collections)} collections found:\n")
    for collection_name in sorted(collections):
        count = db[collection_name].count_documents({})
        try:
            stats = db.command("collStats", collection_name)
            size_mb = stats['size'] / (1024 * 1024)
            print(f"  - {collection_name}: {count:,} records ({size_mb:.2f} MB)")
        except:
            print(f"  - {collection_name}: {count:,} records")

client.close()
print("\n" + "=" * 60)
