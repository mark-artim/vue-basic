from django.db import models

class Product(models.Model):
    """
    Product model - simplified version for testing
    In production, this would connect to your existing MongoDB/ERP
    """
    product_id = models.CharField(max_length=50, unique=True, help_text="Product ID from ERP")
    description = models.TextField(help_text="Product description")
    keywords = models.TextField(blank=True, help_text="Search keywords")
    category = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product_id']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.product_id} - {self.description[:50]}"

    @property
    def display_name(self):
        """For autocomplete display"""
        return f"{self.product_id} - {self.description}"
