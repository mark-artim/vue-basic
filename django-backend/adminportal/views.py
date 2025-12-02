from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from services.erp_client import erp_client, ERPClientError
from services.mongodb_service import mongodb_service
from services.log_service import log_event
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

        # Get the 'next' parameter for redirect after login (from query string or POST data)
        next_url = request.GET.get('next') or data.get('next') or '/admin/dashboard/'
        logger.info(f"[Admin Login] Attempting login for {email}, next_url: {next_url}")

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

        # Log successful admin login to MongoDB
        log_event(
            user_id=user_id,
            user_email=user_email,
            company_id=str(company.get('_id', '')),
            company_code=company_code,
            event_type='login',
            source='django-backend',
            message='Admin user logged in',
            meta={
                'ip': request.META.get('REMOTE_ADDR'),
                'method': 'internal-password',
                'userAgent': request.META.get('HTTP_USER_AGENT', '')
            }
        )

        return JsonResponse({
            'success': True,
            'message': f'Successfully logged in as {user_name}',
            'redirect_url': next_url
        })

    except Exception as e:
        logger.error(f"[Admin Login Error] Unexpected error: {e}")
        return JsonResponse({
            'error': 'Login failed due to server error'
        }, status=500)

def admin_logs_page(request):
    """Admin logs viewer page - requires admin authentication"""
    if not request.session.get('admin_logged_in'):
        return redirect(f'/admin/login/?next={request.path}')

    admin_data = {
        'username': request.session.get('admin_username'),
        'name': request.session.get('admin_name'),
        'email': request.session.get('admin_email'),
        'company_code': request.session.get('admin_company_code'),
    }

    return render(request, 'adminportal/logs.html', {'admin': admin_data})


@csrf_exempt
@require_http_methods(["GET"])
def admin_logs_api(request):
    """
    Admin logs API - returns logs from MongoDB
    Mirrors Node.js GET /logs endpoint

    Query params:
    - type: Filter by log type (login, login-failure, etc.)
    - email: Filter by user email (case-insensitive regex)
    - limit: Number of logs to return (default 100)
    """
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        # Get query parameters
        log_type = request.GET.get('type')
        email = request.GET.get('email')
        limit = int(request.GET.get('limit', 100))

        # Build MongoDB query
        query = {}
        if log_type:
            query['type'] = log_type
        if email:
            query['userEmail'] = {'$regex': email, '$options': 'i'}  # Case-insensitive

        # Query MongoDB logs collection
        db = mongodb_service.db
        logs_collection = db['logs']

        # Fetch logs, sorted by timestamp descending
        logs_cursor = logs_collection.find(query).sort('timestamp', -1).limit(limit)

        # Convert to list and format for JSON response
        logs = []
        for log in logs_cursor:
            log['_id'] = str(log['_id'])  # Convert ObjectId to string
            log['timestamp'] = log['timestamp'].isoformat() if log.get('timestamp') else None
            logs.append(log)

        return JsonResponse(logs, safe=False)

    except Exception as e:
        logger.error(f"[Admin Logs API] Error fetching logs: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to fetch logs'}, status=500)


def admin_dashboard(request):
    """Admin dashboard - requires authentication"""
    if not request.session.get('admin_logged_in'):
        return redirect(f'/admin/login/?next={request.path}')

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
