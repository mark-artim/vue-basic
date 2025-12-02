"""
Authorization decorators for product access control
"""

from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from core.product_registry import get_product
import logging

logger = logging.getLogger(__name__)


def require_product(product_code):
    """
    Decorator to require user to have access to a specific product

    Usage:
        @require_product('product-merge')
        def product_merge_view(request):
            # Only users with 'product-merge' in their authorized products can access
            pass

    Args:
        product_code: Product code from product_registry.py

    Returns:
        Decorator function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is logged in
            is_customer = request.session.get('customer_logged_in', False)
            is_admin = request.session.get('admin_logged_in', False)

            if not is_customer and not is_admin:
                logger.warning(f"[Auth] Unauthenticated access attempt to product: {product_code}")
                return redirect(f'/login/?next={request.path}')

            # Admin users have access to all products
            if is_admin:
                logger.info(f"[Auth] Admin access granted to product: {product_code}")
                return view_func(request, *args, **kwargs)

            # For customer users, check their authorized products
            # In MongoDB, user.products is a list of product codes
            user_products = request.session.get('customer_products', [])

            if product_code in user_products:
                logger.info(f"[Auth] Customer access granted to product: {product_code}")
                return view_func(request, *args, **kwargs)
            else:
                logger.warning(
                    f"[Auth] Customer denied access to product: {product_code}. "
                    f"User products: {user_products}"
                )
                product_info = get_product(product_code)
                product_name = product_info['name'] if product_info else product_code

                # Return HTML response for regular views
                if request.path.endswith('/api/') or '/api/' in request.path:
                    return JsonResponse({
                        'error': 'Access denied',
                        'message': f'You do not have access to {product_name}',
                        'required_product': product_code
                    }, status=403)
                else:
                    # Render unauthorized page or redirect
                    from django.shortcuts import render
                    return render(request, 'unauthorized.html', {
                        'product_name': product_name,
                        'product_code': product_code
                    }, status=403)

        return wrapper
    return decorator


def require_customer_auth(view_func):
    """
    Decorator to require customer authentication (no product check)

    Usage:
        @require_customer_auth
        def dashboard_view(request):
            # Only authenticated customers can access
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('customer_logged_in'):
            logger.warning(f"[Auth] Unauthenticated access attempt to: {request.path}")
            return redirect(f'/login/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_admin_auth(view_func):
    """
    Decorator to require admin authentication

    Usage:
        @require_admin_auth
        def admin_dashboard_view(request):
            # Only authenticated admins can access
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_logged_in'):
            logger.warning(f"[Auth] Unauthenticated admin access attempt to: {request.path}")
            return redirect(f'/admin/login/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper
