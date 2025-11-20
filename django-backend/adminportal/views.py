from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from services.erp_client import erp_client, ERPClientError
from services.mongodb_service import mongodb_service
from decouple import config
import json
import logging
import requests

logger = logging.getLogger(__name__)

def admin_login_page(request):
    """Admin login page - Tailwind version"""
    if request.session.get('admin_logged_in'):
        return redirect('/admin/dashboard/')
    return render(request, 'adminportal/login_tailwind.html')

@csrf_exempt
@require_http_methods(["POST"])
def admin_login_api(request):
    """
    Admin login API - authenticates against MongoDB only
    Mirrors the Node.js admin login flow (bcrypt password verification)
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return JsonResponse({
                'error': 'Email and password are required'
            }, status=400)

        logger.info(f"[Admin Login] Attempting login for {email}")

        # Find user in MongoDB
        user = mongodb_service.find_user_by_email(email)
        if not user:
            logger.warning(f"[Admin Login] User not found: {email}")
            return JsonResponse({
                'error': 'Invalid credentials'
            }, status=401)

        # Check if user is admin
        user_type = user.get('userType')
        if user_type != 'admin':
            logger.warning(f"[Admin Login] Non-admin user attempted login: {email} (type: {user_type})")
            return JsonResponse({
                'error': 'Access denied. Admin accounts only.'
            }, status=403)

        # Verify password using bcrypt (same as Node.js)
        if not mongodb_service.verify_user_password(user, password):
            logger.warning(f"[Admin Login] Invalid password for {email}")
            return JsonResponse({
                'error': 'Invalid credentials'
            }, status=401)

        # Extract user info
        user_id = str(user.get('_id'))
        user_email = user.get('email')
        user_name = user.get('name') or user.get('firstName') or email.split('@')[0]
        company = user.get('companyId', {})
        company_code = company.get('companyCode', 'emp54')

        # Store admin session in Django session
        request.session['admin_logged_in'] = True
        request.session['admin_user_id'] = user_id
        request.session['admin_email'] = user_email
        request.session['admin_username'] = email.split('@')[0]
        request.session['admin_name'] = user_name
        request.session['admin_company_code'] = company_code

        logger.info(f"[Admin Login] ✅ Success for {email} (userType: {user_type})")

        return JsonResponse({
            'success': True,
            'message': f'Successfully logged in as {user_name}',
            'redirect_url': '/admin/dashboard/'
        })

    except Exception as e:
        logger.error(f"[Admin Login Error] Unexpected error: {e}")
        return JsonResponse({
            'error': 'Login failed due to server error'
        }, status=500)

def admin_dashboard(request):
    """Admin dashboard - requires authentication"""
    if not request.session.get('admin_logged_in'):
        return redirect('/admin/login/')

    admin_data = {
        'username': request.session.get('admin_username'),
        'name': request.session.get('admin_name'),
        'email': request.session.get('admin_email'),
        'company_code': request.session.get('admin_company_code'),
    }

    return render(request, 'adminportal/dashboard.html', {'admin': admin_data})

def admin_logout(request):
    """Admin logout"""
    admin_email = request.session.get('admin_email')

    # Clear Django session
    request.session.flush()

    logger.info(f"[Admin Logout] User {admin_email} logged out")
    messages.success(request, 'Successfully logged out')
    return redirect('/admin/login/')

def admin_test_erp(request):
    """Test admin authentication status"""
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    return JsonResponse({
        'status': 'Authenticated as admin',
        'email': request.session.get('admin_email'),
        'name': request.session.get('admin_name'),
        'company_code': request.session.get('admin_company_code'),
        'note': 'Admin users authenticate via MongoDB, not ERP'
    })
