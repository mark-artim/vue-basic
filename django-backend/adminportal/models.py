from django.db import models

class AdminUser(models.Model):
    """
    Admin user model for EMP54 staff
    Separate from Django's built-in User model to match existing Node.js structure
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    erp_username = models.CharField(max_length=100)
    company_id = models.CharField(max_length=100)  # Reference to company in MongoDB
    company_api_base = models.URLField()  # ERP base URL for this company
    last_port = models.CharField(max_length=10, default='5000')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    class Meta:
        db_table = 'admin_users'
