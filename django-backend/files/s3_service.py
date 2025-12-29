"""
Wasabi S3 Service

Handles all interactions with Wasabi object storage.
Enforces company-level file isolation using S3 key prefixes.
"""

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging
import mimetypes
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WasabiS3Service:
    """
    Service for interacting with Wasabi S3 storage.
    All operations are scoped to a specific company for security.
    """

    def __init__(self):
        """Initialize S3 client with Wasabi credentials"""
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.WASABI_ENDPOINT,
            aws_access_key_id=settings.WASABI_ACCESS_KEY,
            aws_secret_access_key=settings.WASABI_SECRET_KEY,
            region_name=settings.WASABI_REGION,
        )
        self.bucket_name = settings.WASABI_BUCKET

    def _get_company_prefix(self, company_code):
        """
        Get the S3 prefix (folder path) for a company.
        This ensures all files are stored in company-specific folders.
        """
        return f"companies/{company_code}/user-uploads/"

    def upload_file(self, file_obj, company_code, filename, content_type=None):
        """
        Upload a file to Wasabi with company isolation.

        Args:
            file_obj: File object or file-like object
            company_code: Company code for isolation
            filename: Desired filename
            content_type: MIME type (auto-detected if not provided)

        Returns:
            dict: {
                'key': str,  # Full S3 key
                'size': int,  # File size in bytes
                'content_type': str
            }
        """
        try:
            # Build S3 key with company prefix
            prefix = self._get_company_prefix(company_code)
            file_key = f"{prefix}{filename}"

            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                content_type = content_type or 'application/octet-stream'

            # Get file size
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset to beginning

            # Upload to Wasabi
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                file_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': {
                        'company_code': company_code,
                        'uploaded_at': datetime.utcnow().isoformat(),
                    }
                }
            )

            logger.info(f"[S3] Uploaded file: {file_key} ({file_size} bytes)")

            return {
                'key': file_key,
                'size': file_size,
                'content_type': content_type,
            }

        except ClientError as e:
            logger.error(f"[S3] Upload failed: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")

    def download_file(self, file_key, company_code):
        """
        Download a file from Wasabi.
        Validates that the file belongs to the specified company.

        Args:
            file_key: S3 key of the file
            company_code: Company code for validation

        Returns:
            bytes: File content

        Raises:
            PermissionError: If file doesn't belong to company
            Exception: If file not found or download fails
        """
        try:
            # SECURITY: Verify file belongs to this company
            if not self._validate_company_access(file_key, company_code):
                logger.warning(f"[S3] Unauthorized access attempt: {company_code} tried to access {file_key}")
                raise PermissionError(f"Access denied: File does not belong to company {company_code}")

            # Download file
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            file_content = response['Body'].read()

            logger.info(f"[S3] Downloaded file: {file_key}")

            return file_content

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise Exception("File not found")
            logger.error(f"[S3] Download failed: {e}")
            raise Exception(f"Failed to download file: {str(e)}")

    def delete_file(self, file_key, company_code):
        """
        Delete a file from Wasabi.
        Validates that the file belongs to the specified company.

        Args:
            file_key: S3 key of the file
            company_code: Company code for validation

        Raises:
            PermissionError: If file doesn't belong to company
        """
        try:
            # SECURITY: Verify file belongs to this company
            if not self._validate_company_access(file_key, company_code):
                logger.warning(f"[S3] Unauthorized delete attempt: {company_code} tried to delete {file_key}")
                raise PermissionError(f"Access denied: File does not belong to company {company_code}")

            # Delete file
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)

            logger.info(f"[S3] Deleted file: {file_key}")

        except ClientError as e:
            logger.error(f"[S3] Delete failed: {e}")
            raise Exception(f"Failed to delete file: {str(e)}")

    def rename_file(self, old_key, new_filename, company_code):
        """
        Rename a file in Wasabi (copy to new key, delete old key).
        Validates that the file belongs to the specified company.

        Args:
            old_key: Current S3 key
            new_filename: New filename (not full path)
            company_code: Company code for validation

        Returns:
            str: New file key
        """
        try:
            # SECURITY: Verify file belongs to this company
            if not self._validate_company_access(old_key, company_code):
                logger.warning(f"[S3] Unauthorized rename attempt: {company_code} tried to rename {old_key}")
                raise PermissionError(f"Access denied: File does not belong to company {company_code}")

            # Build new key with same company prefix
            prefix = self._get_company_prefix(company_code)
            new_key = f"{prefix}{new_filename}"

            # Copy to new key
            copy_source = {'Bucket': self.bucket_name, 'Key': old_key}
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource=copy_source,
                Key=new_key
            )

            # Delete old key
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=old_key)

            logger.info(f"[S3] Renamed file: {old_key} -> {new_key}")

            return new_key

        except ClientError as e:
            logger.error(f"[S3] Rename failed: {e}")
            raise Exception(f"Failed to rename file: {str(e)}")

    def list_files(self, company_code, prefix_filter=''):
        """
        List all files for a specific company.
        Only returns files in the company's folder.

        Args:
            company_code: Company code
            prefix_filter: Optional additional prefix filter within company folder

        Returns:
            list: List of file metadata dicts
        """
        try:
            company_prefix = self._get_company_prefix(company_code)
            full_prefix = company_prefix + prefix_filter

            # List objects with company prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=full_prefix
            )

            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'filename': obj['Key'].replace(company_prefix, ''),
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                    })

            logger.info(f"[S3] Listed {len(files)} files for company {company_code}")

            return files

        except ClientError as e:
            logger.error(f"[S3] List failed: {e}")
            raise Exception(f"Failed to list files: {str(e)}")

    def generate_presigned_url(self, file_key, company_code, expiration=3600):
        """
        Generate a presigned URL for temporary file access.
        Validates company access before generating URL.

        Args:
            file_key: S3 key of the file
            company_code: Company code for validation
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            str: Presigned URL
        """
        try:
            # SECURITY: Verify file belongs to this company
            if not self._validate_company_access(file_key, company_code):
                raise PermissionError(f"Access denied: File does not belong to company {company_code}")

            # Generate presigned URL
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expiration
            )

            logger.info(f"[S3] Generated presigned URL for {file_key} (expires in {expiration}s)")

            return url

        except ClientError as e:
            logger.error(f"[S3] Presigned URL generation failed: {e}")
            raise Exception(f"Failed to generate download URL: {str(e)}")

    def _validate_company_access(self, file_key, company_code):
        """
        Validate that a file belongs to the specified company.
        CRITICAL SECURITY FUNCTION - prevents cross-company access.

        Args:
            file_key: S3 key to validate
            company_code: Company code claiming ownership

        Returns:
            bool: True if file belongs to company, False otherwise
        """
        company_prefix = self._get_company_prefix(company_code)
        return file_key.startswith(company_prefix)


# Singleton instance
_s3_service = None


def get_s3_service():
    """Get singleton instance of WasabiS3Service"""
    global _s3_service
    if _s3_service is None:
        _s3_service = WasabiS3Service()
    return _s3_service
