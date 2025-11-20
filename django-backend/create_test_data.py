#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emp54_django.settings')
django.setup()

from products.models import Product

# Clear existing test data
Product.objects.filter(product_id__in=['96673', '12345', '67890']).delete()

# Create test products
products = [
    {
        'product_id': '96673',
        'description': 'JWH.SS01 STAY-SILV 0% .050X1/8X20 PHOS/CP',
        'keywords': 'SS01 BEN.ADD HA21035 STAY-SI,684032010901',
        'category': 'Welding'
    },
    {
        'product_id': '12345',
        'description': 'Test Product Alpha',
        'keywords': 'test alpha sample demo product',
        'category': 'Testing'
    },
    {
        'product_id': '67890',
        'description': 'Widget Beta Premium',
        'keywords': 'widget beta premium quality high-end',
        'category': 'Widgets'
    }
]

for product_data in products:
    Product.objects.create(**product_data)
    print(f"[OK] Created product: {product_data['product_id']} - {product_data['description'][:30]}...")

print(f"\n[SUCCESS] Successfully created {len(products)} test products!")
print("You can now test the Product Update Merge functionality.")