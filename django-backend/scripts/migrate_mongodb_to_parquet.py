"""
Migration Script: MongoDB to Parquet

Exports MongoDB collections to Parquet files for DuckDB analysis.
Supports both local file output and direct upload to Wasabi S3.

Usage:
    python manage.py shell < scripts/migrate_mongodb_to_parquet.py

Or import and use:
    from scripts.migrate_mongodb_to_parquet import export_collection_to_parquet
    export_collection_to_parquet('purchase_orders', 'purchase_orders.parquet')
"""

import os
import sys
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pymongo import MongoClient
from decouple import config
import boto3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_mongo_client():
    """Get MongoDB client"""
    mongo_uri = config('MONGODB_URI')
    return MongoClient(mongo_uri)


def get_s3_client():
    """Get Wasabi S3 client"""
    return boto3.client(
        's3',
        endpoint_url=f"https://{config('WASABI_ENDPOINT', default='s3.wasabisys.com')}",
        aws_access_key_id=config('WASABI_ACCESS_KEY_ID'),
        aws_secret_access_key=config('WASABI_SECRET_ACCESS_KEY'),
        region_name=config('WASABI_REGION', default='us-east-1')
    )


def export_collection_to_parquet(
    collection_name,
    output_filename,
    database_name=None,
    query=None,
    upload_to_s3=True,
    local_output_dir='./data_exports'
):
    """
    Export a MongoDB collection to Parquet format

    Args:
        collection_name (str): Name of MongoDB collection
        output_filename (str): Output filename (e.g., 'purchase_orders.parquet')
        database_name (str): MongoDB database name (defaults to config)
        query (dict): Optional MongoDB query filter
        upload_to_s3 (bool): Whether to upload to Wasabi S3
        local_output_dir (str): Local directory for output files

    Returns:
        dict: Export statistics
    """
    start_time = datetime.now()

    # Get MongoDB connection
    mongo_client = get_mongo_client()
    db_name = database_name or config('MONGODB_DATABASE', default='emp54')
    db = mongo_client[db_name]
    collection = db[collection_name]

    # Query data
    logger.info(f"Querying MongoDB collection: {collection_name}")
    query = query or {}
    cursor = collection.find(query)

    # Convert to DataFrame
    logger.info("Converting to DataFrame...")
    data = list(cursor)

    if not data:
        logger.warning(f"No data found in collection: {collection_name}")
        return {
            'success': False,
            'message': 'No data found',
            'record_count': 0
        }

    df = pd.DataFrame(data)

    # Convert ObjectId to string (Parquet doesn't support ObjectId)
    if '_id' in df.columns:
        df['_id'] = df['_id'].astype(str)

    # Handle datetime fields
    for col in df.columns:
        if df[col].dtype == 'object':
            # Try to convert to datetime if possible
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore')
            except:
                pass

    record_count = len(df)
    logger.info(f"Loaded {record_count:,} records")

    # Create local output directory
    os.makedirs(local_output_dir, exist_ok=True)
    local_path = os.path.join(local_output_dir, output_filename)

    # Write to Parquet
    logger.info(f"Writing to Parquet: {local_path}")
    table = pa.Table.from_pandas(df)
    pq.write_table(
        table,
        local_path,
        compression='snappy',  # Good balance of speed and compression
        row_group_size=100000  # Optimize for 100K row chunks
    )

    # Get file size
    file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
    logger.info(f"Parquet file size: {file_size_mb:.2f} MB")

    # Upload to S3 if requested
    s3_path = None
    if upload_to_s3:
        try:
            s3_client = get_s3_client()
            bucket = config('WASABI_BUCKET')
            s3_key = f"analytics/{output_filename}"

            logger.info(f"Uploading to s3://{bucket}/{s3_key}")
            s3_client.upload_file(local_path, bucket, s3_key)
            s3_path = f"s3://{bucket}/{s3_key}"
            logger.info(f"Upload complete: {s3_path}")
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            s3_path = None

    # Calculate stats
    elapsed = (datetime.now() - start_time).total_seconds()
    compression_ratio = (file_size_mb / (record_count * 89 / 1024 / 1024)) if record_count > 0 else 0

    stats = {
        'success': True,
        'collection': collection_name,
        'record_count': record_count,
        'file_size_mb': round(file_size_mb, 2),
        'compression_ratio': round(compression_ratio, 2),
        'local_path': local_path,
        's3_path': s3_path,
        'elapsed_seconds': round(elapsed, 2)
    }

    logger.info(f"Export complete: {stats}")
    return stats


def export_all_analytical_collections():
    """
    Export all analytical collections to Parquet

    Customize this function to include your specific collections
    """
    collections = [
        # Example collections - customize based on your needs
        {
            'name': 'purchase_orders',
            'filename': 'purchase_orders.parquet',
            'query': {}  # Export all records
        },
        # Add more collections here as needed
        # {
        #     'name': 'sales_data',
        #     'filename': 'sales_data.parquet',
        #     'query': {'year': {'$gte': 2023}}  # Only recent data
        # },
    ]

    results = []
    for collection_config in collections:
        logger.info(f"\n{'='*60}")
        logger.info(f"Exporting: {collection_config['name']}")
        logger.info(f"{'='*60}")

        result = export_collection_to_parquet(
            collection_name=collection_config['name'],
            output_filename=collection_config['filename'],
            query=collection_config.get('query')
        )
        results.append(result)

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("EXPORT SUMMARY")
    logger.info(f"{'='*60}")
    for result in results:
        if result['success']:
            logger.info(f"{result['collection']}: {result['record_count']:,} records, "
                       f"{result['file_size_mb']} MB, {result['elapsed_seconds']}s")
        else:
            logger.info(f"{result['collection']}: FAILED")

    return results


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Example: Export purchase orders
    print("\n" + "="*60)
    print("MongoDB to Parquet Export Tool")
    print("="*60 + "\n")

    # Uncomment to run export
    # export_collection_to_parquet('purchase_orders', 'purchase_orders.parquet')

    # Or export all configured collections
    # export_all_analytical_collections()

    print("\nTo use this script:")
    print("1. Customize the collection name and query")
    print("2. Run: python manage.py shell < scripts/migrate_mongodb_to_parquet.py")
    print("\nOr import and use directly:")
    print("   from scripts.migrate_mongodb_to_parquet import export_collection_to_parquet")
    print("   export_collection_to_parquet('purchase_orders', 'purchase_orders.parquet')")
