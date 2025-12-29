"""
File Storage Models

Tracks file metadata in database while actual files are stored in Wasabi S3.
Ensures company-level isolation and access control.
"""

from django.db import models
from datetime import datetime


class CompanyFile(models.Model):
    """
    Represents a file uploaded by a company user.
    Files are stored in Wasabi S3 with company-based prefixes for isolation.
    """

    # Django will auto-create 'id' field as primary key

    # File identification
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_key = models.CharField(max_length=500, unique=True)  # Full S3 key path
    file_size = models.BigIntegerField()  # Size in bytes
    content_type = models.CharField(max_length=100)

    # Company isolation - CRITICAL for security
    company_code = models.CharField(max_length=50, db_index=True)
    company_name = models.CharField(max_length=255)

    # User tracking
    uploaded_by_user_id = models.CharField(max_length=100)
    uploaded_by_email = models.CharField(max_length=255)

    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)

    # File categorization (optional)
    category = models.CharField(max_length=100, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Metadata
    description = models.TextField(null=True, blank=True)

    # Soft delete support
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'company_files'
        indexes = [
            models.Index(fields=['company_code', '-uploaded_at']),
            models.Index(fields=['company_code', 'is_deleted']),
        ]

    def __str__(self):
        return f"{self.company_code}/{self.filename}"

    def get_s3_prefix(self):
        """Get the S3 prefix for this company"""
        return f"companies/{self.company_code}/user-uploads/"

    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': str(self.id),
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'uploaded_by': self.uploaded_by_email,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'category': self.category,
            'tags': self.tags,
            'description': self.description,
        }


class FileAccessLog(models.Model):
    """
    Audit log for all file operations.
    Tracks who accessed/modified/deleted files for security and compliance.
    """

    # Django will auto-create 'id' field as primary key

    file_id = models.CharField(max_length=100)  # ObjectId as string
    file_key = models.CharField(max_length=500)

    # Operation details
    operation = models.CharField(max_length=50)  # upload, download, delete, rename

    # User details
    user_id = models.CharField(max_length=100)
    user_email = models.CharField(max_length=255)
    company_code = models.CharField(max_length=50, db_index=True)

    # Request details
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)

    # Result
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'file_access_logs'
        indexes = [
            models.Index(fields=['company_code', '-timestamp']),
            models.Index(fields=['file_id', '-timestamp']),
            models.Index(fields=['operation', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.operation} - {self.file_key} by {self.user_email}"
