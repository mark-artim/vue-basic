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


# ============================================================================
# USER MANAGEMENT
# ============================================================================

def admin_users_page(request):
    """User management page - requires admin authentication"""
    if not request.session.get('admin_logged_in'):
        return redirect(f'/admin/login/?next={request.path}')

    admin_data = {
        'username': request.session.get('admin_username'),
        'name': request.session.get('admin_name'),
        'email': request.session.get('admin_email'),
        'company_code': request.session.get('admin_company_code'),
    }

    return render(request, 'adminportal/users.html', {'admin': admin_data})


@csrf_exempt
@require_http_methods(["GET"])
def admin_users_list_api(request):
    """Get all users with populated company data"""
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        db = mongodb_service.db
        users_collection = db['users']
        companies_collection = db['companies']

        # Get all users
        users = list(users_collection.find())

        # Populate company data
        for user in users:
            user['_id'] = str(user['_id'])

            if user.get('companyId'):
                # Handle both ObjectId and string companyId
                from bson import ObjectId
                company_id = user['companyId']
                if isinstance(company_id, str):
                    company_id = ObjectId(company_id)

                company = companies_collection.find_one({'_id': company_id})
                if company:
                    user['companyId'] = {
                        '_id': str(company['_id']),
                        'name': company.get('name'),
                        'companyCode': company.get('companyCode')
                    }

        return JsonResponse(users, safe=False)

    except Exception as e:
        logger.error(f"[Admin Users List] Error: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to fetch users'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def admin_users_save_api(request):
    """Create or update user"""
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        data = json.loads(request.body)
        from bson import ObjectId
        import bcrypt

        # Extract fields
        user_id = data.get('_id')
        email = data.get('email')
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        user_type = data.get('userType')
        erp_username = data.get('erpUserName', '')
        company_id = data.get('companyId')
        products = data.get('products', [])
        roles = data.get('roles', {})
        password = data.get('password')
        show_unavailable = data.get('showUnavailableProducts', False)

        # Validation
        if not all([email, first_name, last_name, user_type]):
            return JsonResponse({'error': 'Email, firstName, lastName, and userType are required'}, status=400)

        if user_type == 'customer' and not erp_username:
            return JsonResponse({'error': 'ERP username is required for customer users'}, status=400)

        # Build user data
        user_data = {
            'email': email,
            'firstName': first_name,
            'lastName': last_name,
            'userType': user_type,
            'erpUserName': erp_username,
            'products': products,  # ✅ Direct from form - no transformation!
            'roles': roles,
            'showUnavailableProducts': show_unavailable
        }

        # Handle company ID
        if company_id:
            user_data['companyId'] = ObjectId(company_id)

        # Handle password for admin users
        if password and user_type == 'admin':
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user_data['hashedPassword'] = hashed.decode('utf-8')

        db = mongodb_service.db
        users_collection = db['users']

        if user_id:
            # Update existing user
            result = users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': user_data}
            )
            logger.info(f"[Admin Users] Updated user {email}")
        else:
            # Create new user
            # For new admin users, password is required
            if user_type == 'admin' and not password:
                return JsonResponse({'error': 'Password is required for new admin users'}, status=400)

            result = users_collection.insert_one(user_data)
            logger.info(f"[Admin Users] Created user {email}")

        return JsonResponse({'success': True, 'message': 'User saved successfully'})

    except Exception as e:
        logger.error(f"[Admin Users Save] Error: {e}", exc_info=True)
        return JsonResponse({'error': f'Failed to save user: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def admin_users_delete_api(request, user_id):
    """Delete user"""
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        from bson import ObjectId
        db = mongodb_service.db
        users_collection = db['users']

        result = users_collection.delete_one({'_id': ObjectId(user_id)})

        if result.deleted_count > 0:
            logger.info(f"[Admin Users] Deleted user {user_id}")
            return JsonResponse({'success': True, 'message': 'User deleted successfully'})
        else:
            return JsonResponse({'error': 'User not found'}, status=404)

    except Exception as e:
        logger.error(f"[Admin Users Delete] Error: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to delete user'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def admin_companies_list_api(request):
    """Get all companies"""
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        db = mongodb_service.db
        companies_collection = db['companies']
        products_collection = db['products']

        companies = list(companies_collection.find())

        # Convert ObjectId to string and populate products
        for company in companies:
            company['_id'] = str(company['_id'])

            # Get full product details for company's products
            product_codes = company.get('products', [])
            company_products = []
            for code in product_codes:
                product = products_collection.find_one({'_id': code})
                if product:
                    company_products.append({
                        '_id': str(product['_id']),
                        'name': product.get('name', code),
                        'code': code
                    })
            company['products'] = company_products

        return JsonResponse(companies, safe=False)

    except Exception as e:
        logger.error(f"[Admin Companies List] Error: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to fetch companies'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def admin_products_list_api(request):
    """Get all products"""
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        db = mongodb_service.db
        products_collection = db['products']

        products = list(products_collection.find())

        # Convert to simple format
        formatted_products = []
        for product in products:
            formatted_products.append({
                '_id': str(product['_id']),
                'name': product.get('name', product['_id']),
                'description': product.get('description', '')
            })

        return JsonResponse(formatted_products, safe=False)

    except Exception as e:
        logger.error(f"[Admin Products List] Error: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to fetch products'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def admin_send_invite_api(request):
    """Send invite email to user"""
    if not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        import requests
        data = json.loads(request.body)

        to_email = data.get('toEmail')
        user_id = data.get('userId')
        template_type = data.get('templateType', 'standard')

        if not to_email or not user_id:
            return JsonResponse({'error': 'toEmail and userId are required'}, status=400)

        # Forward to Node.js email service
        node_url = 'http://localhost:3001/api/send'
        response = requests.post(node_url, json={
            'toEmail': to_email,
            'userId': user_id,
            'templateType': template_type
        }, timeout=10)

        if response.status_code == 200:
            logger.info(f"[Admin Invite] Sent invite to {to_email}")
            return JsonResponse({'success': True, 'message': 'Invite sent successfully'})
        else:
            error_msg = response.json().get('message', 'Unknown error')
            logger.error(f"[Admin Invite] Failed to send to {to_email}: {error_msg}")
            return JsonResponse({'error': f'Failed to send invite: {error_msg}'}, status=500)

    except Exception as e:
        logger.error(f"[Admin Invite] Error: {e}", exc_info=True)
        return JsonResponse({'error': f'Failed to send invite: {str(e)}'}, status=500)
