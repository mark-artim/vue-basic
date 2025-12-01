"""
Wasabi S3 Client Service

Handles file uploads/downloads to Wasabi object storage
with company-specific folder isolation.
"""

import boto3
import logging
from decouple import config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class WasabiClient:
    """
    Wasabi S3 client for file storage operations
    """

    def __init__(self):
        self.access_key = config('WASABI_ACCESS_KEY')
        self.secret_key = config('WASABI_SECRET_KEY')
        self.bucket_name = config('WASABI_BUCKET_NAME')
        self.region = config('WASABI_REGION', default='us-east-1')
        self.endpoint = config('WASABI_ENDPOINT', default='https://s3.wasabisys.com')

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint,
            region_name=self.region
        )

        logger.info(f"[Wasabi] Initialized client for bucket: {self.bucket_name}")

    def upload_file(self, file_path, s3_key):
        """
        Upload a file to Wasabi

        Args:
            file_path: Local file path to upload
            s3_key: S3 object key (path in bucket)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            logger.info(f"[Wasabi] ✅ Uploaded {file_path} to {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"[Wasabi] ❌ Upload failed: {e}")
            return False

    def download_file(self, s3_key, local_path):
        """
        Download a file from Wasabi

        Args:
            s3_key: S3 object key (path in bucket)
            local_path: Local file path to save to

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"[Wasabi] ✅ Downloaded {s3_key} to {local_path}")
            return True
        except ClientError as e:
            logger.error(f"[Wasabi] ❌ Download failed: {e}")
            return False

    def list_files(self, prefix=''):
        """
        List files in Wasabi bucket with optional prefix

        Args:
            prefix: S3 key prefix to filter by

        Returns:
            list: List of S3 object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
                logger.info(f"[Wasabi] Found {len(files)} files with prefix '{prefix}'")
                return files
            else:
                logger.info(f"[Wasabi] No files found with prefix '{prefix}'")
                return []
        except ClientError as e:
            logger.error(f"[Wasabi] ❌ List files failed: {e}")
            return []

    def delete_file(self, s3_key):
        """
        Delete a file from Wasabi

        Args:
            s3_key: S3 object key to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"[Wasabi] ✅ Deleted {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"[Wasabi] ❌ Delete failed: {e}")
            return False

    def move_file(self, source_key, dest_key):
        """
        Move a file within Wasabi bucket (copy + delete)

        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Copy object
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': source_key},
                Key=dest_key
            )
            # Delete original
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=source_key)
            logger.info(f"[Wasabi] ✅ Moved {source_key} to {dest_key}")
            return True
        except ClientError as e:
            logger.error(f"[Wasabi] ❌ Move failed: {e}")
            return False


# Global instance
wasabi_client = WasabiClient()
