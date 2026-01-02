# DuckDB Migration Guide

## Overview

This guide helps you migrate from MongoDB-based analytics to DuckDB + Parquet for **10-100x faster queries** and **90%+ cost savings** on large analytical datasets.

## Current vs. Proposed Architecture

### Current (MongoDB)
```
User uploads CSV (111K rows)
    ↓
Django processes & inserts to MongoDB Atlas
    ↓
MongoDB stores 9.9MB of data
    ↓
Query via MongoDB aggregation pipeline
    ↓
Cost: $9-57/month as data grows
```

### Proposed (DuckDB + Parquet)
```
User uploads CSV (111K rows)
    ↓
Django converts to Parquet & uploads to Wasabi
    ↓
Wasabi stores ~3-5MB compressed Parquet
    ↓
Query with DuckDB directly from Wasabi
    ↓
Cost: ~$0.01/month for storage
Query speed: 10-100x faster than MongoDB
```

## Why DuckDB for Your Use Case?

✅ **Perfect fit** because you have:
- Read-only analysis (no updates/deletes needed)
- One-way data loads (monthly updates)
- Large datasets (111K-2M rows)
- Structured data (CSV exports from ERP)

✅ **Benefits:**
- **No database server** - runs in Django process
- **Query directly from S3/Wasabi** - no data loading
- **SQL interface** - familiar syntax
- **Blazing fast** - optimized for analytics
- **Free** - no licensing or hosting costs

## Installation

Already added to `requirements.txt`:
```txt
duckdb==1.1.3
pyarrow==18.1.0
```

Install locally:
```bash
cd django-backend
pip install duckdb pyarrow
```

## Step 1: Export Existing MongoDB Data to Parquet

### Option A: Using the Migration Script

```bash
cd django-backend
python manage.py shell
```

```python
from scripts.migrate_mongodb_to_parquet import export_collection_to_parquet

# Export purchase orders from MongoDB to Parquet
stats = export_collection_to_parquet(
    collection_name='purchase_orders',
    output_filename='purchase_orders.parquet',
    upload_to_s3=True
)

print(f"Exported {stats['record_count']:,} records")
print(f"File size: {stats['file_size_mb']} MB")
print(f"S3 path: {stats['s3_path']}")
```

### Option B: Manual Export with Pandas

```python
from pymongo import MongoClient
import pandas as pd
import pyarrow.parquet as pq
from decouple import config

# Get data from MongoDB
mongo_client = MongoClient(config('MONGODB_URI'))
db = mongo_client[config('MONGODB_DATABASE', default='emp54')]
pos = list(db.purchase_orders.find())

# Convert to DataFrame
df = pd.DataFrame(pos)
df['_id'] = df['_id'].astype(str)  # Convert ObjectId to string

# Write to Parquet
pq.write_table(
    pa.Table.from_pandas(df),
    'purchase_orders.parquet',
    compression='snappy'
)

print(f"Exported {len(df):,} records")
```

## Step 2: Query with DuckDB

### Example 1: Basic Query

```python
from services.duckdb_client import duckdb_client

# Query Parquet file directly from Wasabi
results = duckdb_client.query("""
    SELECT
        vendor,
        COUNT(*) as order_count,
        SUM(amount) as total_spent
    FROM 's3://your-bucket/analytics/purchase_orders.parquet'
    GROUP BY vendor
    ORDER BY total_spent DESC
    LIMIT 10
""")

print(f"Found {len(results)} vendors")
```

### Example 2: Time-Series Analysis

```python
# Monthly spending trends
results = duckdb_client.query("""
    SELECT
        DATE_TRUNC('month', order_date) as month,
        SUM(amount) as monthly_total,
        COUNT(*) as order_count,
        AVG(amount) as avg_order_value
    FROM 's3://your-bucket/analytics/purchase_orders.parquet'
    WHERE order_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', order_date)
    ORDER BY month DESC
""")
```

### Example 3: Complex Aggregation

```python
# Top vendors by category
results = duckdb_client.query("""
    WITH vendor_stats AS (
        SELECT
            vendor,
            category,
            SUM(amount) as total,
            COUNT(*) as orders,
            RANK() OVER (PARTITION BY category ORDER BY SUM(amount) DESC) as rank
        FROM 's3://your-bucket/analytics/purchase_orders.parquet'
        GROUP BY vendor, category
    )
    SELECT * FROM vendor_stats
    WHERE rank <= 5
    ORDER BY category, rank
""")
```

## Step 3: Integrate into Django Views

### Example: Purchase Order Analytics Endpoint

```python
# analytics/views_duckdb.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from services.duckdb_client import duckdb_client
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def vendor_analysis(request):
    """Analyze vendor spending with DuckDB"""
    if not request.session.get('customer_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        # Get query parameters
        start_date = request.GET.get('start_date', '2020-01-01')
        end_date = request.GET.get('end_date', '2030-12-31')
        min_orders = int(request.GET.get('min_orders', 1))

        # Query with DuckDB (blazing fast!)
        parquet_path = duckdb_client.get_s3_path('analytics/purchase_orders.parquet')

        results = duckdb_client.query(f"""
            SELECT
                vendor,
                COUNT(*) as order_count,
                SUM(amount) as total_spent,
                AVG(amount) as avg_order,
                MIN(order_date) as first_order,
                MAX(order_date) as last_order
            FROM '{parquet_path}'
            WHERE order_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY vendor
            HAVING COUNT(*) >= {min_orders}
            ORDER BY total_spent DESC
        """)

        return JsonResponse({
            'success': True,
            'data': results,
            'record_count': len(results)
        })

    except Exception as e:
        logger.error(f"Vendor analysis error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
```

## Step 4: Update CSV Import Flow

### Current Flow (MongoDB)
```python
# analytics/views.py - Current approach
def import_pos(request):
    # Parse CSV
    # Insert into MongoDB
    analytics_mongodb.bulk_insert(records)
```

### New Flow (Parquet)
```python
# analytics/views_duckdb.py - New approach
import pyarrow as pa
import pyarrow.parquet as pq

def import_pos_to_parquet(request):
    """Import CSV directly to Parquet, skip MongoDB"""
    csv_file = request.FILES['file']

    # Parse CSV with pandas
    df = pd.read_csv(csv_file)

    # Clean/validate data
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['order_date'] = pd.to_datetime(df['order_date'])

    # Write to Parquet
    output_path = f"po_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    table = pa.Table.from_pandas(df)
    pq.write_table(table, output_path, compression='snappy')

    # Upload to Wasabi
    s3_client = get_s3_client()
    s3_client.upload_file(
        output_path,
        config('WASABI_BUCKET'),
        f'analytics/{output_path}'
    )

    return JsonResponse({
        'success': True,
        'records': len(df),
        'file': output_path
    })
```

## Step 5: Performance Comparison

### MongoDB Aggregation (Current)
```python
# Query 111K records
import time
start = time.time()

pipeline = [
    {'$group': {
        '_id': '$vendor',
        'total': {'$sum': '$amount'},
        'count': {'$sum': 1}
    }},
    {'$sort': {'total': -1}},
    {'$limit': 100}
]
results = list(db.purchase_orders.aggregate(pipeline))

print(f"MongoDB: {time.time() - start:.3f}s")
# Typical: 2-5 seconds for 111K records
```

### DuckDB (New)
```python
# Query same 111K records
start = time.time()

results = duckdb_client.query("""
    SELECT vendor, SUM(amount) as total, COUNT(*) as count
    FROM 's3://bucket/purchase_orders.parquet'
    GROUP BY vendor
    ORDER BY total DESC
    LIMIT 100
""")

print(f"DuckDB: {time.time() - start:.3f}s")
# Typical: 0.05-0.2 seconds (10-100x faster!)
```

## Migration Checklist

- [ ] Install duckdb and pyarrow (`pip install duckdb pyarrow`)
- [ ] Test DuckDB client with sample query
- [ ] Export existing MongoDB data to Parquet (one collection)
- [ ] Upload Parquet to Wasabi
- [ ] Create test Django view using DuckDB
- [ ] Compare query performance (MongoDB vs DuckDB)
- [ ] Update CSV import flow to write Parquet instead of MongoDB
- [ ] Migrate all analytical collections
- [ ] Update frontend to use new DuckDB endpoints
- [ ] Remove MongoDB analytical data (keep users/companies/auth)
- [ ] Celebrate 90%+ cost savings! 🎉

## Cost Comparison

### MongoDB Atlas (Current Path)
- Free M0: 512MB (you'll exceed this soon)
- M2 Shared: $9/month for 2GB
- M10 Dedicated: $57/month for 10GB
- **Estimated for 2M records: $57-97/month**

### DuckDB + Wasabi (Proposed)
- Wasabi storage: $0.0059/GB/month
- 2M records ≈ 150MB compressed Parquet
- **Total cost: ~$0.01/month** 🎯

**Annual savings: ~$684-1,164** for analytical data alone!

## Frequently Asked Questions

### Can I keep MongoDB for some data?

**Yes!** Keep MongoDB for:
- Users, companies, products (operational data)
- Session management
- Authentication tokens
- Any data that needs frequent updates

Use DuckDB for:
- Purchase orders (read-only analysis)
- Sales data (historical reporting)
- Transfer analysis (large CSV exports)
- Any analytical workload

### What if I need to update records?

DuckDB Parquet files are **immutable** - you can't update individual records. Instead:

**Option 1:** Replace the entire Parquet file (works great for monthly refreshes)

**Option 2:** Use partitioned Parquet files by date:
```
s3://bucket/analytics/pos/year=2024/month=01/data.parquet
s3://bucket/analytics/pos/year=2024/month=02/data.parquet
```

**Option 3:** Use PostgreSQL for data that needs frequent updates

### Can DuckDB handle 2 million rows?

Absolutely! DuckDB is designed for **billions** of rows. 2M is small for DuckDB:
- 2M rows: ~50-200ms query time
- 20M rows: ~200-500ms query time
- 200M rows: ~1-2s query time

### What about real-time data?

For real-time dashboards, combine approaches:
- **Recent data (last 7 days):** MongoDB or PostgreSQL
- **Historical data:** DuckDB + Parquet

Query both with UNION or merge in Django:
```python
# Get last 7 days from MongoDB
recent = list(db.purchase_orders.find({'date': {'$gte': week_ago}}))

# Get historical from DuckDB
historical = duckdb_client.query("""
    SELECT * FROM 's3://bucket/pos.parquet'
    WHERE date < current_date - 7
""")

# Merge in Python
all_data = recent + historical
```

## Next Steps

1. **Test the setup:**
   ```bash
   cd django-backend
   python manage.py shell
   from services.duckdb_client import duckdb_client
   print("DuckDB ready!" if duckdb_client else "Error")
   ```

2. **Export one collection:**
   ```python
   from scripts.migrate_mongodb_to_parquet import export_collection_to_parquet
   export_collection_to_parquet('purchase_orders', 'purchase_orders.parquet')
   ```

3. **Run a test query:**
   ```python
   results = duckdb_client.query("SELECT COUNT(*) as count FROM 'purchase_orders.parquet'")
   print(f"Record count: {results[0]['count']:,}")
   ```

4. **Measure performance and decide!**

## Support

Questions? The DuckDB client is in `services/duckdb_client.py` with full documentation.

Migration script: `scripts/migrate_mongodb_to_parquet.py`

Example views: See code snippets above or create `analytics/views_duckdb.py`

---

**TL;DR:** DuckDB + Parquet = Fast queries + Low cost + Happy developers 🚀
