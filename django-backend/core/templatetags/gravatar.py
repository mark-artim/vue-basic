from django import template
from core.product_registry import get_product, get_user_products
import hashlib

register = template.Library()

@register.filter
def gravatar_hash(email):
    """Generate MD5 hash for Gravatar URL"""
    if not email:
        return ''
    return hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()


@register.simple_tag(takes_context=True)
def user_has_product(context, product_code):
    """
    Check if current user has access to a product

    Usage in templates:
        {% user_has_product 'product-merge' as has_access %}
        {% if has_access %}
            <a href="/products/merge/">Product Merge</a>
        {% endif %}

    Or directly in if statement:
        {% if user_has_product 'product-merge' %}
            ...
        {% endif %}
    """
    request = context.get('request')
    if not request:
        return False

    # Admins have access to all products
    if request.session.get('admin_logged_in'):
        return True

    # Check customer products
    user_products = request.session.get('customer_products', [])
    return product_code in user_products


@register.simple_tag(takes_context=True)
def get_authorized_products(context):
    """
    Get list of products user has access to

    Usage in templates:
        {% get_authorized_products as products %}
        {% for product in products %}
            <a href="{{ product.url }}">{{ product.name }}</a>
        {% endfor %}
    """
    request = context.get('request')
    if not request:
        return []

    # Admins get all products
    if request.session.get('admin_logged_in'):
        from core.product_registry import get_active_products
        return list(get_active_products().values())

    # Customers get only their authorized products
    user_products = request.session.get('customer_products', [])
    return get_user_products(user_products)


@register.simple_tag
def get_product_info(product_code):
    """
    Get product metadata by code

    Usage:
        {% get_product_info 'product-merge' as product %}
        {{ product.name }} - {{ product.description }}
    """
    return get_product(product_code)
