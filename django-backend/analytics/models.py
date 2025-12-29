"""
PO Analytics Models

Stores purchase order data in MongoDB for analytics queries.
"""

from django.db import models
from datetime import datetime
import uuid


class PurchaseOrder(models.Model):
    """
    Purchase Order record for analytics.
    Imported from CSV files, stored in MongoDB.
    """

    # PO Details
    po_payto_id = models.CharField(max_length=50, db_index=True)
    po_payto_name = models.CharField(max_length=255, db_index=True)
    po_company = models.CharField(max_length=50, db_index=True)
    po_branch = models.CharField(max_length=50, db_index=True)
    po_number = models.CharField(max_length=50, unique=True)

    # Financial Data
    order_total = models.DecimalField(max_digits=15, decimal_places=2)
    order_date = models.DateField(db_index=True)

    # Company Isolation
    company_code = models.CharField(max_length=50, db_index=True)

    # Import Metadata
    import_batch_id = models.CharField(max_length=100, db_index=True, default='legacy')  # UUID for batch operations
    imported_at = models.DateTimeField(auto_now_add=True)
    imported_by_email = models.CharField(max_length=255)
    source_file = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'purchase_orders'
        indexes = [
            models.Index(fields=['company_code', 'po_payto_name', '-order_date']),
            models.Index(fields=['company_code', 'po_branch', '-order_date']),
            models.Index(fields=['company_code', 'po_company', '-order_date']),
            models.Index(fields=['company_code', '-order_date']),
        ]
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.po_number} - {self.po_payto_name} - ${self.order_total}"

    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': str(self.id),
            'po_payto_id': self.po_payto_id,
            'po_payto_name': self.po_payto_name,
            'po_company': self.po_company,
            'po_branch': self.po_branch,
            'po_number': self.po_number,
            'order_total': float(self.order_total),
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'company_code': self.company_code,
        }


class ImportLog(models.Model):
    """
    Tracks CSV import operations for audit trail.
    """

    # Import Details
    import_batch_id = models.CharField(max_length=100, db_index=True, default=uuid.uuid4)  # UUID (not unique to allow legacy imports)
    filename = models.CharField(max_length=500)
    file_key = models.CharField(max_length=500)
    company_code = models.CharField(max_length=50, db_index=True)

    # Results
    total_rows = models.IntegerField(default=0)
    imported_rows = models.IntegerField(default=0)
    skipped_rows = models.IntegerField(default=0)
    error_rows = models.IntegerField(default=0)

    # User Tracking
    imported_by_email = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)

    # Status
    status = models.CharField(max_length=50)  # processing, completed, failed
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'po_import_logs'
        ordering = ['-imported_at']

    def __str__(self):
        return f"{self.filename} - {self.status} ({self.imported_rows}/{self.total_rows})"

    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': str(self.id),
            'import_batch_id': self.import_batch_id,
            'filename': self.filename,
            'company_code': self.company_code,
            'total_rows': self.total_rows,
            'imported_rows': self.imported_rows,
            'skipped_rows': self.skipped_rows,
            'error_rows': self.error_rows,
            'imported_by': self.imported_by_email,
            'imported_at': self.imported_at.isoformat() if self.imported_at else None,
            'status': self.status,
            'error_message': self.error_message,
        }
