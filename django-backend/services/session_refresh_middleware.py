"""
Session Refresh Middleware

Automatically checks and refreshes ERP sessions before they expire.
Runs before every request to ensure session is valid.
"""

import logging
from django.shortcuts import redirect
from django.http import JsonResponse
from services.erp_client import erp_client

logger = logging.getLogger(__name__)


class SessionRefreshMiddleware:
    """
    Middleware to automatically refresh ERP sessions before they expire
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only check for authenticated customer users
        if request.session.get('customer_logged_in') and request.session.get('customer_user_type') == 'customer':
            # Check and refresh session if needed
            session_valid = erp_client.check_and_refresh_session(request)

            if not session_valid:
                # Session refresh failed, redirect to login
                logger.warning(f"[Session Middleware] Session refresh failed for user {request.session.get('customer_email')}, logging out")

                # Clear session
                request.session.flush()

                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                    return JsonResponse({
                        'success': False,
                        'error': 'Session expired. Please log in again.',
                        'redirect': '/login/'
                    }, status=401)
                else:
                    return redirect('/login/?expired=true')

        response = self.get_response(request)
        return response
