"""
Parquet-based CSV Import for Purchase Orders

This replaces the MongoDB import flow with a Parquet-based approach:
1. Upload CSV
2. Convert to Parquet
3. Upload to Wasabi S3
4. Optionally append to existing data or replace

Benefits:
- 30x compression
- No database writes
- Instant querying with DuckDB
- ~$0.01/month storage cost
"""

import os
import io
import uuid
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from decimal import Decimal
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from decouple import config
import boto3

logger = logging.getLogger(__name__)

# Wasabi S3 configuration
WASABI_BUCKET = config('WASABI_BUCKET')
WASABI_ENDPOINT = config('WASABI_ENDPOINT')
WASABI_ACCESS_KEY = config('WASABI_ACCESS_KEY')
WASABI_SECRET_KEY = config('WASABI_SECRET_KEY')
WASABI_REGION = config('WASABI_REGION')

PARQUET_PATH = 'analytics/purchase_orders.parquet'


def get_s3_client():
    """Get configured Wasabi S3 client"""
    return boto3.client(
        's3',
        endpoint_url=WASABI_ENDPOINT,
        aws_access_key_id=WASABI_ACCESS_KEY,
        aws_secret_access_key=WASABI_SECRET_KEY,
        region_name=WASABI_REGION
    )


@require_http_methods(["POST"])
def import_csv_to_parquet(request):
    """
    Import CSV and convert to Parquet for DuckDB analytics

    POST params:
        - file: CSV file upload
        - skip_rows: Number of rows to skip before headers (default: 0)
        - mode: 'replace' or 'append' (default: 'append')
        - batch_name: Optional name for this import (default: filename)

    Returns:
        - success: bool
        - import_id: Unique import ID
        - records_imported: Number of records
        - file_size_mb: Parquet file size
        - s3_path: S3 location
    """
    try:
        # Check authentication
        if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

        # Get user session data
        user_email = request.session.get('customer_email') or request.session.get('admin_username', 'unknown')
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Get uploaded file
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)

        uploaded_file = request.FILES['file']
        filename = uploaded_file.name

        # Validate CSV file
        if not filename.endswith('.csv'):
            return JsonResponse({'success': False, 'error': 'Only CSV files are supported'}, status=400)

        # Get parameters
        skip_rows = int(request.POST.get('skip_rows', 0))
        mode = request.POST.get('mode', 'append')  # 'replace' or 'append'
        batch_name = request.POST.get('batch_name', filename)

        import_id = str(uuid.uuid4())

        logger.info(f"Starting Parquet import: {filename} (mode={mode}, skip_rows={skip_rows})")

        # Step 1: Read CSV into DataFrame
        try:
            df = pd.read_csv(
                io.BytesIO(uploaded_file.read()),
                skiprows=skip_rows,
                encoding='utf-8'
            )
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'CSV parsing error: {str(e)}'}, status=400)

        if df.empty:
            return JsonResponse({'success': False, 'error': 'CSV file is empty'}, status=400)

        # Step 2: Validate and normalize column names
        # Expected columns (case-insensitive)
        expected_cols = {
            'po_payto_id': ['po_payto_id', 'payto_id', 'vendor_id'],
            'po_payto_name': ['po_payto_name', 'payto_name', 'vendor_name', 'vendor'],
            'po_company': ['po_company', 'company'],
            'po_branch': ['po_branch', 'branch'],
            'po_number': ['po_number', 'po#', 'po_no', 'purchase_order'],
            'order_total': ['order_total', 'total', 'amount'],
            'order_date': ['order_date', 'date', 'po_date']
        }

        # Normalize column names (lowercase, strip whitespace)
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

        # Map columns to expected names
        column_mapping = {}
        for target_col, possible_names in expected_cols.items():
            for col in df.columns:
                if col in possible_names:
                    column_mapping[col] = target_col
                    break

        df.rename(columns=column_mapping, inplace=True)

        # Verify required columns exist
        required = ['po_payto_name', 'po_number', 'order_total']
        missing = [col for col in required if col not in df.columns]

        if missing:
            return JsonResponse({
                'success': False,
                'error': f'Missing required columns: {", ".join(missing)}. Found: {", ".join(df.columns)}'
            }, status=400)

        # Step 3: Clean and validate data
        # Convert order_total to numeric
        df['order_total'] = pd.to_numeric(df['order_total'], errors='coerce')

        # Convert order_date to datetime
        if 'order_date' in df.columns:
            df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')

        # Add metadata columns
        df['company_code'] = company_code
        df['import_batch_id'] = import_id
        df['imported_by'] = user_email
        df['imported_at'] = datetime.now()

        # Remove rows with null required fields
        df = df.dropna(subset=['po_number', 'order_total'])

        if df.empty:
            return JsonResponse({'success': False, 'error': 'No valid records after data cleaning'}, status=400)

        record_count = len(df)
        logger.info(f"Processed {record_count} valid records from CSV")

        # Step 4: Handle append mode - merge with existing Parquet
        s3_client = get_s3_client()

        if mode == 'append':
            # Try to read existing Parquet file
            try:
                response = s3_client.get_object(Bucket=WASABI_BUCKET, Key=PARQUET_PATH)
                existing_df = pd.read_parquet(io.BytesIO(response['Body'].read()))

                logger.info(f"Found existing Parquet with {len(existing_df)} records")

                # Append new data
                df = pd.concat([existing_df, df], ignore_index=True)

                logger.info(f"Combined: {len(df)} total records")

            except s3_client.exceptions.NoSuchKey:
                logger.info("No existing Parquet file found, creating new one")
            except Exception as e:
                logger.warning(f"Could not read existing Parquet: {e}, creating new file")

        # Step 5: Write to Parquet
        logger.info("Converting to Parquet with Snappy compression...")

        # Create temporary file
        temp_file = f'/tmp/po_import_{import_id}.parquet'

        table = pa.Table.from_pandas(df)
        pq.write_table(
            table,
            temp_file,
            compression='snappy',
            row_group_size=100000
        )

        file_size_mb = os.path.getsize(temp_file) / (1024 * 1024)

        logger.info(f"Parquet file created: {file_size_mb:.2f} MB")

        # Step 6: Upload to Wasabi
        logger.info(f"Uploading to s3://{WASABI_BUCKET}/{PARQUET_PATH}")

        s3_client.upload_file(
            temp_file,
            WASABI_BUCKET,
            PARQUET_PATH,
            ExtraArgs={'ContentType': 'application/octet-stream'}
        )

        # Clean up temp file
        os.remove(temp_file)

        s3_path = f"s3://{WASABI_BUCKET}/{PARQUET_PATH}"

        logger.info(f"Upload complete: {s3_path}")

        # Step 7: Return success response
        return JsonResponse({
            'success': True,
            'import_id': import_id,
            'message': f'Successfully imported {record_count} records to Parquet',
            'records_imported': record_count,
            'total_records': len(df),
            'file_size_mb': round(file_size_mb, 2),
            's3_path': s3_path,
            'mode': mode,
            'batch_name': batch_name,
            'columns': list(df.columns),
            'duckdb_endpoint': '/analytics/duckdb/summary/'
        })

    except Exception as e:
        logger.error(f"Parquet import error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def parquet_file_info(request):
    """
    Get information about the current Parquet file

    Returns:
        - exists: bool
        - file_size_mb: float
        - last_modified: ISO timestamp
        - s3_path: string
    """
    try:
        s3_client = get_s3_client()

        # Get file metadata
        response = s3_client.head_object(Bucket=WASABI_BUCKET, Key=PARQUET_PATH)

        return JsonResponse({
            'success': True,
            'exists': True,
            'file_size_mb': round(response['ContentLength'] / (1024 * 1024), 2),
            'last_modified': response['LastModified'].isoformat(),
            's3_path': f"s3://{WASABI_BUCKET}/{PARQUET_PATH}"
        })

    except s3_client.exceptions.NoSuchKey:
        return JsonResponse({
            'success': True,
            'exists': False,
            'message': 'No Parquet file found'
        })

    except Exception as e:
        logger.error(f"Error getting Parquet file info: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def replace_parquet_file(request):
    """
    Replace existing Parquet file (convenience wrapper for import with mode=replace)
    """
    request.POST = request.POST.copy()  # Make mutable
    request.POST['mode'] = 'replace'
    return import_csv_to_parquet(request)
