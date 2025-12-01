"""
Django management command to fetch warehouse queue CSV files from email

Usage: python manage.py fetch_warehouse_emails
"""

import os
import re
import tempfile
import logging
from django.core.management.base import BaseCommand
from decouple import config
from imap_tools import MailBox, AND
from services.wasabi_client import wasabi_client

logger = logging.getLogger(__name__)

# Company code mapping (from email subject [CODE] to folder name)
COMPANY_CODE_MAP = {
    'HERITAGE': 'heritage',
    'METRO': 'metro',
    'TRISTATE': 'tristate',
    'WITTICHEN': 'wittichen',
}


class Command(BaseCommand):
    help = 'Fetch warehouse queue CSV files from Zoho email and upload to Wasabi'

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write('[Warehouse Email] Starting email fetch process...')

        # Get email credentials from environment
        email_address = config('ZOHO_EMAIL')
        email_password = config('ZOHO_PASSWORD')
        imap_server = config('ZOHO_IMAP_SERVER', default='imap.zoho.com')

        processed_count = 0
        error_count = 0

        try:
            # Connect to Zoho IMAP
            with MailBox(imap_server).login(
                email_address,
                email_password,
                initial_folder='IMPORT'
            ) as mailbox:

                self.stdout.write('[Warehouse Email] Connected to IMAP server')

                # Fetch unread emails
                messages = list(mailbox.fetch(AND(seen=False), reverse=True))
                self.stdout.write(f'[Warehouse Email] Found {len(messages)} unread emails')

                for msg in messages:
                    try:
                        self.stdout.write(f'\n[Warehouse Email] Processing email:')
                        self.stdout.write(f'  From: {msg.from_}')
                        self.stdout.write(f'  Subject: {msg.subject}')

                        # Extract company code from subject [HERITAGE], [METRO], etc.
                        company_code = self._extract_company_code(msg.subject)

                        if not company_code:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  ⚠️  No company code found in subject, using fallback'
                                )
                            )
                            company_code = '_unassigned'

                        # Process CSV attachments
                        csv_count = 0
                        for att in msg.attachments:
                            if att.filename.lower().endswith('.csv'):
                                csv_count += 1
                                self._process_attachment(att, company_code)

                        if csv_count > 0:
                            # Move email to PROCESSED folder
                            mailbox.move(msg.uid, 'PROCESSED')
                            processed_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✅ Processed {csv_count} CSV file(s), moved to PROCESSED'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING('  ⚠️  No CSV attachments found')
                            )

                    except Exception as e:
                        error_count += 1
                        logger.error(f'[Warehouse Email] Error processing email: {e}', exc_info=True)
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Error: {str(e)}')
                        )

        except Exception as e:
            logger.error(f'[Warehouse Email] Fatal error: {e}', exc_info=True)
            self.stdout.write(
                self.style.ERROR(f'\n❌ Fatal error: {str(e)}')
            )
            return

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Email fetch complete: {processed_count} processed, {error_count} errors'
            )
        )

    def _extract_company_code(self, subject):
        """
        Extract company code from email subject [HERITAGE] → 'heritage'

        Args:
            subject: Email subject line

        Returns:
            str: Company folder name or None if not found
        """
        match = re.search(r'\[([A-Z0-9_]+)\]', subject)
        if match:
            code = match.group(1).upper()
            return COMPANY_CODE_MAP.get(code)
        return None

    def _process_attachment(self, attachment, company_code):
        """
        Save CSV attachment to temp file and upload to Wasabi

        Args:
            attachment: imap-tools Attachment object
            company_code: Company folder name (e.g., 'heritage')
        """
        filename = attachment.filename
        self.stdout.write(f'  📎 Attachment: {filename}')

        # Create temp file to save CSV
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as temp_file:
            temp_path = temp_file.name
            temp_file.write(attachment.payload)

        try:
            # Upload to Wasabi: data/uploads/{company}/upload/warehouse_queue.csv
            # Always use 'warehouse_queue.csv' as the standardized name
            s3_key = f'data/uploads/{company_code}/upload/warehouse_queue.csv'

            self.stdout.write(f'  ☁️  Uploading to Wasabi: {s3_key}')

            success = wasabi_client.upload_file(temp_path, s3_key)

            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Uploaded successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Upload failed')
                )

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
