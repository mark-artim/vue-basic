"""
Django management command to process warehouse queue CSV files from Wasabi into MongoDB

Usage: python manage.py process_warehouse_csv [--company=heritage]
"""

import os
import csv
import tempfile
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from pymongo import MongoClient
from decouple import config
from services.wasabi_client import wasabi_client

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process warehouse queue CSV files from Wasabi and load into MongoDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Process only this company (e.g., heritage, metro)',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        target_company = options.get('company')

        if target_company:
            self.stdout.write(f'[Warehouse CSV] Processing company: {target_company}')
            companies = [target_company]
        else:
            self.stdout.write('[Warehouse CSV] Processing all companies')
            # Process all known companies
            companies = ['heritage', 'metro', 'tristate', 'wittichen']

        # Connect to MongoDB
        mongo_uri = config('MONGO_URI')
        db_name = config('DB_NAME', default='emp54')

        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db['warehouse_invoices']

        self.stdout.write(f'[Warehouse CSV] Connected to MongoDB: {db_name}')

        total_processed = 0
        total_errors = 0

        for company_code in companies:
            try:
                processed, errors = self._process_company(company_code, collection)
                total_processed += processed
                total_errors += errors
            except Exception as e:
                logger.error(f'[Warehouse CSV] Error processing {company_code}: {e}', exc_info=True)
                self.stdout.write(
                    self.style.ERROR(f'❌ Error processing {company_code}: {str(e)}')
                )
                total_errors += 1

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ CSV processing complete: {total_processed} records, {total_errors} errors'
            )
        )

    def _process_company(self, company_code, collection):
        """
        Process warehouse CSV for a single company

        Args:
            company_code: Company folder name (e.g., 'heritage')
            collection: MongoDB collection

        Returns:
            tuple: (processed_count, error_count)
        """
        self.stdout.write(f'\n[{company_code.upper()}] Processing warehouse queue...')

        # Download CSV from Wasabi
        s3_key = f'data/uploads/{company_code}/upload/warehouse_queue.csv'
        self.stdout.write(f'  Downloading: {s3_key}')

        # Check if file exists
        files = wasabi_client.list_files(prefix=s3_key)
        if not files or s3_key not in files:
            self.stdout.write(
                self.style.WARNING(f'  ⚠️  No CSV file found, skipping')
            )
            return 0, 0

        # Download to temp file
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.csv') as temp_file:
            temp_path = temp_file.name

        try:
            success = wasabi_client.download_file(s3_key, temp_path)

            if not success:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Download failed')
                )
                return 0, 1

            # Parse CSV and load into MongoDB
            processed_count = self._parse_and_load_csv(temp_path, company_code, collection)

            # Move to processed folder on Wasabi
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_key = f'data/uploads/{company_code}/processed/warehouse_queue_{timestamp}.csv'

            self.stdout.write(f'  Moving to: {dest_key}')
            wasabi_client.move_file(s3_key, dest_key)

            self.stdout.write(
                self.style.SUCCESS(f'  ✅ Processed {processed_count} records')
            )

            return processed_count, 0

        except Exception as e:
            logger.error(f'[Warehouse CSV] Error processing {company_code}: {e}', exc_info=True)
            self.stdout.write(
                self.style.ERROR(f'  ❌ Error: {str(e)}')
            )
            return 0, 1

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _parse_and_load_csv(self, csv_path, company_code, collection):
        """
        Parse CSV file and load records into MongoDB

        Args:
            csv_path: Path to CSV file
            company_code: Company folder name
            collection: MongoDB collection

        Returns:
            int: Number of records processed
        """
        self.stdout.write(f'  Parsing CSV...')

        records = []

        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            # Read all lines and filter out blank lines
            lines = [line for line in csvfile if line.strip()]

            # Read first line and strip whitespace from column names
            csvfile.seek(0)
            first_line = csvfile.readline()
            fieldnames = [name.strip() for name in first_line.split(',')]

            # Create DictReader with cleaned fieldnames
            reader = csv.DictReader(csvfile, fieldnames=fieldnames, skipinitialspace=True)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                # Skip empty rows (can happen with blank lines)
                if not any(row.values()):
                    continue

                # Map Eclipse CSV columns to MongoDB document
                # Actual CSV columns: FULL.OID, BR, PRT, SHIP.VIA

                full_oid = row.get('FULL.OID', '').strip()
                branch = row.get('BR', '').strip()
                print_status = row.get('PRT', '').strip()
                ship_via = row.get('SHIP.VIA', '').strip()

                # Skip records with missing FULL.OID
                if not full_oid:
                    logger.warning(f'[Warehouse CSV] Row {row_num}: Skipping - missing FULL.OID')
                    continue

                record = {
                    'companyCode': company_code,
                    'fullInvoiceID': full_oid,
                    'branch': branch,
                    'printStatus': print_status,
                    'shipVia': ship_via,
                    'lastUpdated': datetime.utcnow(),
                }

                records.append(record)

        if not records:
            self.stdout.write(
                self.style.WARNING(f'  ⚠️  No valid records found in CSV')
            )
            return 0

        self.stdout.write(f'  Parsed {len(records)} valid records')

        # Clear existing records for this company (replace, not append)
        delete_result = collection.delete_many({'companyCode': company_code})
        self.stdout.write(f'  Cleared {delete_result.deleted_count} existing records')

        # Insert new records
        insert_result = collection.insert_many(records)
        inserted_count = len(insert_result.inserted_ids)

        self.stdout.write(f'  Inserted {inserted_count} new records')

        return inserted_count
