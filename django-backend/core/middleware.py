"""
Authorization middleware for automatic product access control

This middleware automatically checks if users have access to product URLs
without requiring decorators on every view.
"""

from django.shortcuts import redirect, render
from django.http import JsonResponse
from core.product_registry import get_product_by_url, get_product
import logging

logger = logging.getLogger(__name__)


class ProductAuthorizationMiddleware:
    """
    Middleware to check product authorization for all requests

    This runs before view functions and checks if the requested URL
    requires product authorization.
    """

    # URLs that don't require product checks
    EXEMPT_URLS = [
        '/login/',
        '/admin/login/',
        '/logout/',
        '/admin/logout/',
        '/dashboard/',
        '/admin/dashboard/',
        '/static/',
        '/media/',
        '/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if URL requires product authorization
        path = request.path

        # Skip exempt URLs
        if any(path.startswith(exempt) for exempt in self.EXEMPT_URLS):
            return self.get_response(request)

        # Check if this URL maps to a product
        product_code = get_product_by_url(path)

        if product_code:
            # This URL requires product authorization
            is_customer = request.session.get('customer_logged_in', False)
            is_admin = request.session.get('admin_logged_in', False)

            # Must be logged in
            if not is_customer and not is_admin:
                logger.warning(f"[Middleware] Unauthenticated access attempt to: {path}")
                return redirect(f'/login/?next={path}')

            # Admins have access to all products
            if is_admin:
                logger.debug(f"[Middleware] Admin access granted to: {path}")
                return self.get_response(request)

            # Check customer authorization
            user_products = request.session.get('customer_products', [])

            if product_code not in user_products:
                logger.warning(
                    f"[Middleware] Customer denied access to: {path} "
                    f"(product: {product_code}, user products: {user_products})"
                )

                product_info = get_product(product_code)
                product_name = product_info['name'] if product_info else product_code

                # API requests get JSON response
                if '/api/' in path or path.endswith('/api/'):
                    return JsonResponse({
                        'error': 'Access denied',
                        'message': f'You do not have access to {product_name}',
                        'required_product': product_code
                    }, status=403)

                # Regular requests get unauthorized page
                return render(request, 'unauthorized.html', {
                    'product_name': product_name,
                    'product_code': product_code
                }, status=403)

            logger.debug(f"[Middleware] Customer access granted to: {path}")

        # Continue to view
        return self.get_response(request)
