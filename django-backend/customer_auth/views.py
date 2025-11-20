from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from services.mongodb_service import mongodb_service
from services.erp_client import erp_client, ERPClientError
import json
import logging
import requests

logger = logging.getLogger(__name__)

def customer_login_page(request):
    """Customer login page - Tailwind version"""
    if request.session.get('customer_logged_in'):
        return redirect('/dashboard/')
    return render(request, 'customer_auth/login_tailwind.html')

@csrf_exempt
@require_http_methods(["POST"])
def customer_login_api(request):
    """
    Customer login API - Mirrors Node.js auth flow exactly:
    1. Find user by email in MongoDB
    2. Get company info from MongoDB
    3. Authenticate with ERP using company's API URL
    4. Store ERP token in Redis
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({
                'error': 'Email and password are required'
            }, status=400)

        logger.info(f"[Customer Login] Attempting login for email: {email}")

        # Step 1: Find user by email in MongoDB (like Node.js User.findOne({ email }).populate('companyId'))
        user = mongodb_service.find_user_by_email(email)
        if not user:
            logger.info(f"[Customer Login] User not found: {email}")
            return JsonResponse({'error': 'User not found'}, status=404)

        logger.info(f"[Customer Login] Found user: {email}, userType: {user.get('userType')}")

        user_type = user.get('userType')

        if user_type == 'admin':
            # Handle admin users (similar to Node.js flow)
            if not mongodb_service.verify_user_password(user, password):
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

            # Store admin session
            request.session['customer_logged_in'] = True
            request.session['customer_user_id'] = str(user['_id'])
            request.session['customer_email'] = email
            request.session['customer_user_type'] = 'admin'

            logger.info(f"[Customer Login] Admin login successful: {email}")

            return JsonResponse({
                'success': True,
                'message': f'Admin login successful for {email}',
                'redirect_url': '/dashboard/',
                'user_type': 'admin'
            })

        elif user_type == 'customer':
            # Step 2: Get ERP connection info
            erp_info = mongodb_service.get_user_erp_info(user)

            erp_username = erp_info.get('erp_username')
            company_api_base = erp_info.get('company_api_base')
            last_port = erp_info.get('last_port', '5000')
            company_code = erp_info.get('company_code')
            user_id = erp_info.get('user_id')

            if not all([erp_username, company_api_base, user_id]):
                logger.error(f"[Customer Login] Missing ERP info for {email}")
                return JsonResponse({
                    'error': 'Incomplete user configuration. Please contact support.'
                }, status=400)

            logger.info(f"[Customer Login] Using ERP: {company_api_base}:{last_port}, erp_username: {erp_username}")

            # Step 3: Authenticate with ERP (exactly like Node.js)
            try:
                erp_login_url = f"{company_api_base}:{last_port}/Sessions"

                logger.info(f"[Customer Login] Calling ERP login: {erp_login_url}")

                erp_response = requests.post(erp_login_url, json={
                    'username': erp_username,
                    'password': password
                }, timeout=30)

                erp_response.raise_for_status()
                erp_data = erp_response.json()

                logger.info(f"[Customer Login] ERP Response received for {email}")

                erp_token = erp_data.get('sessionToken')
                if not erp_token:
                    logger.error('[Customer Login] Missing ERP session token in response')
                    return JsonResponse({
                        'error': 'Missing ERP session token from ERP server'
                    }, status=401)

                # Step 4: Store ERP token in Redis (same as Node.js)
                redis_key = f"erpToken:{user_id}"
                redis_success = erp_client._redis_set(redis_key, erp_token, 7200)  # 2 hours TTL

                if redis_success:
                    logger.info(f"[Customer Login] ✅ Stored ERP token in Redis for {user_id}")
                else:
                    logger.warning("[Customer Login] Redis not available, token stored in session only")

                # Step 5: Get user's name from ERP
                user_name = None
                try:
                    user_data = erp_client.get_user(
                        user_id=user_id,
                        company_api_base=company_api_base,
                        port=int(last_port)
                    )
                    user_name = user_data.get('name') or user_data.get('firstName') or user_data.get('username')
                    logger.info(f"[Customer Login] Retrieved user name from ERP: {user_name}")
                except Exception as e:
                    logger.warning(f"[Customer Login] Could not fetch user name from ERP: {e}")
                    user_name = email.split('@')[0]  # Fallback to email username

                # Get user's authorized products from MongoDB
                user_products = user.get('products', [])
                logger.info(f"[Customer Login] User authorized products: {user_products}")

                # Store customer session
                request.session['customer_logged_in'] = True
                request.session['customer_user_id'] = user_id
                request.session['customer_email'] = email
                request.session['customer_name'] = user_name
                request.session['customer_user_type'] = 'customer'
                request.session['customer_erp_username'] = erp_username
                request.session['customer_company_api_base'] = company_api_base
                request.session['customer_last_port'] = last_port
                request.session['customer_company_code'] = company_code
                request.session['customer_products'] = user_products  # Product authorization
                request.session['customer_erp_token'] = erp_token  # Backup

                logger.info(f"[Customer Login] ✅ Customer login successful: {email} via ERP")

                return JsonResponse({
                    'success': True,
                    'message': f'Successfully logged in as {email}',
                    'redirect_url': '/dashboard/',
                    'user_type': 'customer',
                    'company_code': company_code
                })

            except requests.exceptions.RequestException as e:
                error_msg = f"ERP login failed: {str(e)}"
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_data = e.response.json()
                        error_msg = f"ERP login failed: {error_data}"
                    except:
                        error_msg = f"ERP login failed: HTTP {e.response.status_code}"

                logger.error(f"[Customer Login] {error_msg}")
                return JsonResponse({'error': error_msg}, status=401)

        else:
            return JsonResponse({'error': f'Unknown user type: {user_type}'}, status=400)

    except Exception as e:
        logger.error(f"[Customer Login] Unexpected error: {e}")
        return JsonResponse({
            'error': 'Login failed due to server error'
        }, status=500)

def customer_dashboard(request):
    """Customer dashboard - requires authentication"""
    if not request.session.get('customer_logged_in'):
        return redirect('/login/')

    # Get user from MongoDB to get API ports and last port
    customer_email = request.session.get('customer_email')
    user = mongodb_service.find_user_by_email(customer_email)

    # Extract API ports from company record
    api_ports = []
    if user and user.get('companyId') and isinstance(user['companyId'], dict):
        api_ports = user['companyId'].get('apiPorts', ['5000'])

    customer_data = {
        'email': request.session.get('customer_email'),
        'user_type': request.session.get('customer_user_type'),
        'company_code': request.session.get('customer_company_code'),
        'erp_username': request.session.get('customer_erp_username'),
        'last_port': user.get('lastPort', '5000') if user else '5000',
        'api_ports': json.dumps(api_ports),  # Convert to JSON for JavaScript
    }

    return render(request, 'customer_auth/dashboard.html', {'customer': customer_data})

def customer_home_tailwind(request):
    """Customer home page with Tailwind - shows product cards"""
    if not request.session.get('customer_logged_in'):
        return redirect('/login/')

    # Get user from MongoDB
    customer_email = request.session.get('customer_email')
    user = mongodb_service.find_user_by_email(customer_email)

    # Get all products from MongoDB
    try:
        all_products_collection = mongodb_service.db.products
        all_products_docs = list(all_products_collection.find({}))
    except Exception as e:
        logger.error(f"[Home Tailwind] Error fetching products: {e}")
        all_products_docs = []

    # Get user's subscribed products from their JWT/session
    user_product_codes = user.get('products', []) if user else []

    # Separate into authorized and available
    authorized_products = []
    available_products = []

    for product in all_products_docs:
        product_data = {
            'code': str(product.get('_id')),
            'name': product.get('name', product.get('_id')),
            'description': product.get('description'),
            'longDescription': product.get('longDescription'),
            'features': product.get('features', []),
        }

        if str(product.get('_id')) in user_product_codes:
            authorized_products.append(product_data)
        else:
            available_products.append(product_data)

    context = {
        'authorized_products': authorized_products,
        'available_products': available_products,
    }

    return render(request, 'home_tailwind.html', context)

def customer_logout(request):
    """Customer logout"""
    # Clear ERP token from Redis if available
    customer_user_id = request.session.get('customer_user_id')
    if customer_user_id:
        redis_key = f"erpToken:{customer_user_id}"
        redis_success = erp_client._redis_delete(redis_key)

        if redis_success:
            logger.info(f"[Customer Logout] Cleared ERP token from Redis for {customer_user_id}")
        else:
            logger.error(f"[Customer Logout] Redis error: Failed to delete token for {customer_user_id}")

    # Clear Django session
    request.session.flush()
    messages.success(request, 'Successfully logged out')
    return redirect('/login/')

def customer_test_erp(request):
    """Test ERP connectivity using customer session"""
    if not request.session.get('customer_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    customer_user_id = request.session.get('customer_user_id')
    company_api_base = request.session.get('customer_company_api_base')
    last_port = request.session.get('customer_last_port')

    try:
        # Test ERP connection using customer credentials
        from services.product_service import product_service

        products = product_service.search_products(
            user_id=customer_user_id,
            company_api_base=company_api_base,
            keyword="test",
            port=int(last_port)
        )

        return JsonResponse({
            'status': 'ERP connection successful',
            'products_found': len(products),
            'sample_products': products[:3] if products else [],
            'customer_email': request.session.get('customer_email'),
            'company_code': request.session.get('customer_company_code')
        })

    except ERPClientError as e:
        return JsonResponse({
            'status': 'ERP connection failed',
            'error': str(e)
        }, status=500)

@csrf_exempt
def customer_update_port(request):
    """Update customer's lastPort in MongoDB"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.session.get('customer_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        data = json.loads(request.body)
        new_port = data.get('port')

        if not new_port:
            return JsonResponse({'error': 'Port is required'}, status=400)

        # Get user from MongoDB
        customer_email = request.session.get('customer_email')
        user = mongodb_service.find_user_by_email(customer_email)

        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)

        # Update lastPort in MongoDB
        success = mongodb_service.update_user_port(user['_id'], new_port)

        if success:
            # Update session data
            request.session['customer_last_port'] = new_port
            logger.info(f"[Port Update] Updated port to {new_port} for user {customer_email}")
            return JsonResponse({'success': True, 'port': new_port})
        else:
            return JsonResponse({'error': 'Failed to update port'}, status=500)

    except Exception as e:
        logger.error(f"[Port Update] Error: {e}")
        return JsonResponse({'error': 'Failed to update port'}, status=500)
