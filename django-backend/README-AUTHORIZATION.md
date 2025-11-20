# Product Authorization System

This Django backend uses a product-based authorization system similar to the Vue frontend. Users belong to companies and are authorized for specific products.

## Architecture Overview

```
User (MongoDB) → has products[] → Product Registry → URL Protection
```

## Core Components

### 1. Product Registry (`core/product_registry.py`)

Central configuration for all EMP54 products:

```python
PRODUCTS = {
    'product-merge': {
        'code': 'product-merge',
        'name': 'Product Update Merge',
        'url': '/products/merge/',
        'active': True,
    },
    'pdw-data-prep': {
        'code': 'pdw-data-prep',
        'name': 'PDW Data Prep',
        'url': '/pdw/',
        'active': False,
    },
}
```

### 2. Authorization Decorators (`core/decorators.py`)

Protect individual views:

```python
from core.decorators import require_product

@require_product('product-merge')
def product_merge_view(request):
    # Only users with 'product-merge' in their products[] can access
    pass
```

**Available decorators:**
- `@require_product(product_code)` - Requires specific product
- `@require_customer_auth` - Requires customer login (any product)
- `@require_admin_auth` - Requires admin login

### 3. Authorization Middleware (`core/middleware.py`)

Automatic URL protection without decorators:

- Checks all requests against product registry
- Redirects unauthorized users to `/unauthorized/`
- Admins bypass all checks
- Exempt URLs: `/login/`, `/dashboard/`, `/static/`, etc.

### 4. Template Tags (`core/templatetags/gravatar.py`)

Show/hide UI elements based on product access:

```django
{% load gravatar %}

{# Check if user has product #}
{% user_has_product 'product-merge' as has_merge %}
{% if has_merge %}
    <a href="/products/merge/">Product Merge</a>
{% endif %}

{# Get all authorized products #}
{% get_authorized_products as products %}
{% for product in products %}
    <a href="{{ product.url }}">{{ product.name }}</a>
{% endfor %}

{# Get product info #}
{% get_product_info 'pdw-data-prep' as product %}
{{ product.name }} - {{ product.description }}
```

## User Flow

### Customer Login

1. User logs in at `/login/`
2. System finds user in MongoDB
3. User document has `products: ['product-merge', 'pdw-data-prep']`
4. Session stores `customer_products` list
5. Middleware checks all requests against this list

### Admin Login

1. Admin logs in at `/admin/login/` with ERP credentials
2. Admins have access to **all products** automatically
3. No product checking occurs for admin sessions

## MongoDB User Schema

Users must have `products` array in MongoDB:

```javascript
{
  _id: ObjectId("..."),
  email: "user@company.com",
  companyId: ObjectId("..."),
  products: ["product-merge", "pdw-data-prep", "shipstation"],
  userType: "customer"
}
```

## Adding a New Product

1. **Add to Product Registry** (`core/product_registry.py`):

```python
PRODUCTS = {
    'my-new-feature': {
        'code': 'my-new-feature',
        'name': 'My New Feature',
        'description': 'Does something cool',
        'icon': 'star',
        'url': '/my-feature/',
        'category': 'tools',
        'active': True,
    },
}

URL_TO_PRODUCT = {
    '/my-feature/': 'my-new-feature',
}
```

2. **Create View** (optional decorator if middleware not used):

```python
from core.decorators import require_product

@require_product('my-new-feature')
def my_feature_view(request):
    return render(request, 'my_feature.html')
```

3. **Add to URLs**:

```python
urlpatterns = [
    path('my-feature/', my_feature_view, name='my_feature'),
]
```

4. **Add to user in MongoDB**:

```javascript
db.users.updateOne(
  { email: "user@company.com" },
  { $push: { products: "my-new-feature" } }
)
```

## Authorization Flow Diagram

```
Request to /products/merge/
    ↓
Middleware checks URL → Product Registry
    ↓
Is user logged in? → No → Redirect /login/
    ↓ Yes
Is user admin? → Yes → Allow access ✓
    ↓ No
Check session['customer_products']
    ↓
'product-merge' in products? → No → Show /unauthorized/
    ↓ Yes
Allow access ✓
```

## Testing Authorization

### Test customer with products:

```python
# In Django shell or view
request.session['customer_logged_in'] = True
request.session['customer_products'] = ['product-merge']

# Try to access /products/merge/ → ✓ Allowed
# Try to access /pdw/ → ✗ Denied (unauthorized.html)
```

### Test admin access:

```python
request.session['admin_logged_in'] = True

# Try to access any product → ✓ All allowed
```

## Error Handling

**Unauthorized access returns:**
- **HTML requests**: `unauthorized.html` template (403)
- **API requests**: JSON error (403)

```json
{
  "error": "Access denied",
  "message": "You do not have access to Product Update Merge",
  "required_product": "product-merge"
}
```

## Security Notes

- Product checks happen **before** view execution
- Session data is server-side (not client-modifiable)
- Admins bypass checks (use admin role carefully)
- MongoDB `products` array is source of truth

## Migration from Vue

This system mirrors the Vue frontend:

| Vue | Django |
|-----|--------|
| `authStore.userProducts` | `request.session['customer_products']` |
| Router guards | Middleware + Decorators |
| `v-if="hasProduct('code')"` | `{% user_has_product 'code' %}` |
| Products in Pinia | Products in Product Registry |

## Future Enhancements

- [ ] Product permissions (read/write/admin)
- [ ] Time-based product access (trial periods)
- [ ] Usage tracking per product
- [ ] Product feature flags
