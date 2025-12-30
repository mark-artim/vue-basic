"""
Product Registry - Central configuration for all EMP54 products

This maps product codes to their metadata, URLs, and authorization requirements.
Similar to the Vue frontend product configuration.
"""

PRODUCTS = {
    'product-merge': {
        'code': 'product-merge',
        'name': 'Product Update Merge',
        'description': 'Merge product keywords with real ERP data integration',
        'icon': 'box-seam',
        'url': '/products/merge/',
        'category': 'products',
        'active': True,
    },
    'product-search': {
        'code': 'product-search',
        'name': 'Product Search',
        'description': 'Search through your ERP product database',
        'icon': 'search',
        'url': '/products/search/',
        'category': 'products',
        'active': True,
    },
    'product-compare': {
        'code': 'eclipse',
        'name': 'Product Comparison',
        'description': 'Upload CSV to compare two products side-by-side',
        'icon': 'arrow-left-right',
        'url': '/products/compare/',
        'category': 'eclipse',
        'active': True,
    },
    'pdw-data-prep': {
        'code': 'pdw-data-prep',
        'name': 'PDW Data Prep',
        'description': 'Upload and clean Excel files for PDW import',
        'icon': 'file-spreadsheet',
        'url': '/pdw/',
        'category': 'data-tools',
        'active': True,
    },
    'file-manager': {
        'code': 'eclipse',
        'name': 'File Manager',
        'description': 'Securely upload, download, and manage company files',
        'icon': 'folder-fill',
        'url': '/files/',
        'category': 'eclipse',
        'active': True,
    },
    'invoice-lookup': {
        'code': 'eclipse',
        'name': 'Invoice Lookup',
        'description': 'Search customer invoices and view PDFs',
        'icon': 'file-text',
        'url': '/invoices/lookup/',
        'category': 'eclipse',
        'active': True,
    },
    'branch-transfer-analysis': {
        'code': 'eclipse',
        'name': 'Branch Transfer Analysis',
        'description': 'Analyze branch-to-branch transfers by buyline from CSV data',
        'icon': 'diagram-3',
        'url': '/branch/transfers/',
        'category': 'eclipse',
        'active': True,
    },
    'shipstation': {
        'code': 'shipstation',
        'name': 'ShipStation Integration',
        'description': 'Manage shipping and order fulfillment',
        'icon': 'truck',
        'url': '/shipping/',
        'category': 'shipping',
        'active': False,  # Not yet in Django
    },
    'reports': {
        'code': 'reports',
        'name': 'Reports & Analytics',
        'description': 'Generate ERP reports and analytics',
        'icon': 'graph-up',
        'url': '/reports/',
        'category': 'analytics',
        'active': False,  # Coming soon
    },
}

# URL pattern to product code mapping (for middleware)
URL_TO_PRODUCT = {
    '/products/merge/': 'product-merge',
    '/products/search/': 'product-search',
    '/products/compare/': 'eclipse',
    '/pdw/': 'pdw-data-prep',
    '/files/': 'eclipse',
    '/invoices/': 'eclipse',
    '/branch/': 'eclipse',
    '/shipping/': 'shipstation',
    '/reports/': 'reports',
}

def get_product(product_code):
    """Get product metadata by code"""
    return PRODUCTS.get(product_code)

def get_all_products():
    """Get all products"""
    return PRODUCTS

def get_active_products():
    """Get only active/implemented products"""
    return {code: data for code, data in PRODUCTS.items() if data['active']}

def get_product_by_url(url):
    """Get product code by URL pattern"""
    # Check exact match first
    if url in URL_TO_PRODUCT:
        return URL_TO_PRODUCT[url]

    # Check if URL starts with any registered pattern
    for pattern, code in URL_TO_PRODUCT.items():
        if url.startswith(pattern):
            return code

    return None

def get_user_products(user_products_list):
    """
    Get product metadata for user's authorized products

    Args:
        user_products_list: List of product codes from MongoDB user document

    Returns:
        List of product metadata dicts
    """
    return [PRODUCTS[code] for code in user_products_list if code in PRODUCTS]
