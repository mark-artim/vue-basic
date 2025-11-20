from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from core.decorators import require_product
from services.product_service import product_service
from services.erp_client import ERPClientError
from decouple import config
import json
import logging

logger = logging.getLogger(__name__)

def product_merge_page(request):
    """Main page for product update merge functionality"""
    return render(request, 'products/merge_tailwind.html')

@require_product('eclipse')
def product_compare_page(request):
    """Product comparison page - Upload CSV and compare products side-by-side"""
    return render(request, 'products/compare.html')

def product_get_api(request, product_id):
    """
    API endpoint to get a single product by ID using real ERP integration
    """
    try:
        # Check if user is authenticated via customer login
        if request.session.get('customer_logged_in'):
            # Use customer session data
            user_id = request.session.get('customer_user_id')
            company_api_base = request.session.get('customer_company_api_base')
            port = int(request.session.get('customer_last_port', 5000))
            logger.info(f"[Product Get] Using customer session: {user_id}")
        elif request.session.get('admin_logged_in'):
            # Use admin session data
            user_id = request.session.get('admin_user_id')
            company_api_base = request.session.get('admin_company_api_base')
            port = int(request.session.get('admin_port', 5000))
            logger.info(f"[Product Get] Using admin session: {user_id}")
        else:
            # Fallback to environment configuration for testing
            user_id = config('DEFAULT_USER_ID', default='demo_user')
            company_api_base = config('DEFAULT_COMPANY_API_BASE', default='http://your-erp-server.com')
            port = config('DEFAULT_ERP_PORT', default=5000, cast=int)
            logger.warning(f"[Product Get] No session found, using demo credentials: {user_id}")

        if not all([user_id, company_api_base]):
            return JsonResponse({
                'error': 'Authentication required. Please log in.'
            }, status=401)

        # Call real ERP via product service
        product = product_service.get_product(
            user_id=user_id,
            company_api_base=company_api_base,
            product_id=product_id,
            port=port
        )

        if not product:
            return JsonResponse({
                'error': 'Product not found',
                'id': product_id
            }, status=404)

        return JsonResponse(product)

    except ERPClientError as e:
        error_message = str(e)
        logger.error(f"ERP get product failed for ID '{product_id}': {e}")

        # Check if it's a 404 (product not found) - return proper 404 instead of 500
        if '404' in error_message or 'not found' in error_message.lower():
            return JsonResponse({
                'id': product_id,
                'error': 'Product not found',
                'description': 'Not found',
                'upc': 'N/A',
                'priceLineId': 'N/A',
                'buyLineId': 'N/A'
            }, status=200)  # Return 200 with error fields so frontend doesn't break

        return JsonResponse({
            'error': 'ERP request failed',
            'details': str(e)
        }, status=500)

    except Exception as e:
        logger.error(f"Unexpected error in product get: {e}")
        return JsonResponse({
            'error': 'Failed to retrieve product',
            'details': str(e)
        }, status=500)

def product_search_api(request):
    """
    API endpoint for product search using real ERP integration
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'products': []})

    try:
        # Check if user is authenticated via customer login
        if request.session.get('customer_logged_in'):
            # Use customer session data
            user_id = request.session.get('customer_user_id')
            company_api_base = request.session.get('customer_company_api_base')
            port = int(request.session.get('customer_last_port', 5000))
            logger.info(f"[Product Search] Using customer session: {user_id}")
        elif request.session.get('admin_logged_in'):
            # Use admin session data
            user_id = request.session.get('admin_user_id')
            company_api_base = request.session.get('admin_company_api_base')
            port = int(request.session.get('admin_port', 5000))
            logger.info(f"[Product Search] Using admin session: {user_id}")
        else:
            # Fallback to environment configuration for testing
            user_id = config('DEFAULT_USER_ID', default='demo_user')
            company_api_base = config('DEFAULT_COMPANY_API_BASE', default='http://your-erp-server.com')
            port = config('DEFAULT_ERP_PORT', default=5000, cast=int)
            logger.warning(f"[Product Search] No session found, using demo credentials: {user_id}")

        if not all([user_id, company_api_base]):
            return JsonResponse({
                'error': 'Authentication required. Please log in.',
                'products': []
            }, status=401)

        # Call real ERP via product service
        products = product_service.search_products(
            user_id=user_id,
            company_api_base=company_api_base,
            keyword=query,
            include_inactive=True,
            page_size=10,
            port=port
        )

        return JsonResponse({'products': products})

    except ERPClientError as e:
        logger.error(f"ERP search failed for query '{query}': {e}")
        return JsonResponse({
            'error': 'ERP search failed',
            'details': str(e),
            'products': []
        }, status=500)

    except Exception as e:
        logger.error(f"Unexpected error in product search: {e}")
        return JsonResponse({
            'error': 'Search failed',
            'details': str(e),
            'products': []
        }, status=500)

@csrf_exempt
def product_merge_save(request):
    """
    Save the merged product keywords using real ERP integration
    """
    if request.method != 'POST':
        logger.error(f"[Product Merge Save] Method not allowed: {request.method}")
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        logger.info(f"[Product Merge Save] Starting merge save request")
        logger.info(f"[Product Merge Save] Request body: {request.body}")

        data = json.loads(request.body)
        keeper_id = data.get('keeper_id')
        merge_id = data.get('merge_id')
        selected_companies = data.get('selected_companies', {})

        logger.info(f"[Product Merge Save] Keeper ID: {keeper_id}, Merge ID: {merge_id}")
        logger.info(f"[Product Merge Save] Selected companies: {selected_companies}")

        if not keeper_id or not merge_id:
            logger.error(f"[Product Merge Save] Missing IDs - keeper: {keeper_id}, merge: {merge_id}")
            return JsonResponse({
                'error': 'Both keeper and merge product IDs required'
            }, status=400)

        # Check if user is authenticated via customer login
        if request.session.get('customer_logged_in'):
            # Use customer session data
            user_id = request.session.get('customer_user_id')
            company_api_base = request.session.get('customer_company_api_base')
            port = int(request.session.get('customer_last_port', 5000))
            logger.info(f"[Product Merge Save] Using customer session: {user_id}, port: {port}")
        elif request.session.get('admin_logged_in'):
            # Use admin session data
            user_id = request.session.get('admin_user_id')
            company_api_base = request.session.get('admin_company_api_base')
            port = int(request.session.get('admin_port', 5000))
            logger.info(f"[Product Merge Save] Using admin session: {user_id}, port: {port}")
        else:
            # Fallback to environment configuration for testing
            user_id = config('DEFAULT_USER_ID', default='demo_user')
            company_api_base = config('DEFAULT_COMPANY_API_BASE', default='http://your-erp-server.com')
            port = config('DEFAULT_ERP_PORT', default=5000, cast=int)
            logger.warning(f"[Product Merge Save] No session found, using demo credentials: {user_id}")

        if not all([user_id, company_api_base]):
            logger.error(f"[Product Merge Save] Missing auth - user_id: {user_id}, api_base: {company_api_base}")
            return JsonResponse({
                'error': 'Authentication required. Please log in.'
            }, status=401)

        logger.info(f"[Product Merge Save] Calling ERP merge with user: {user_id}, port: {port}")

        # Call real ERP via product service
        result = product_service.merge_product_keywords(
            user_id=user_id,
            company_api_base=company_api_base,
            keeper_product_id=keeper_id,
            merge_product_id=merge_id,
            selected_companies=selected_companies,
            port=port
        )

        logger.info(f"[Product Merge Save] ERP merge successful: {result}")

        return JsonResponse({
            'success': result['success'],
            'keeper_id': result['keeper_id'],
            'updated_keywords': result['updated_keywords'],
            'message': f'Successfully merged keywords for product {keeper_id} via ERP',
            'debug_info': result.get('debug_info', {}),
            'prod_class_response': result.get('prod_class_response', {}),
            'product_response': result.get('product_response', {})
        })

    except ERPClientError as e:
        logger.error(f"[Product Merge Save] ERP merge failed for {keeper_id} + {merge_id}: {e}")
        return JsonResponse({
            'error': 'ERP merge failed',
            'details': str(e)
        }, status=500)

    except Exception as e:
        logger.error(f"[Product Merge Save] Unexpected error in product merge: {e}")
        logger.error(f"[Product Merge Save] Exception type: {type(e)}")
        import traceback
        logger.error(f"[Product Merge Save] Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'error': 'Merge failed',
            'details': str(e)
        }, status=500)

# Development/testing views with real ERP connection
def test_erp_connection(request):
    """Test view to verify ERP connectivity with real credentials"""
    try:
        # Check if user is authenticated via customer login
        if request.session.get('customer_logged_in'):
            # Use customer session data
            user_id = request.session.get('customer_user_id')
            company_api_base = request.session.get('customer_company_api_base')
            port = int(request.session.get('customer_last_port', 5000))
            logger.info(f"[Test ERP] Using customer session: {user_id}")
        elif request.session.get('admin_logged_in'):
            # Use admin session data
            user_id = request.session.get('admin_user_id')
            company_api_base = request.session.get('admin_company_api_base')
            port = int(request.session.get('admin_port', 5000))
            logger.info(f"[Test ERP] Using admin session: {user_id}")
        else:
            # Fallback to environment configuration for testing
            user_id = config('DEFAULT_USER_ID', default='demo_user')
            company_api_base = config('DEFAULT_COMPANY_API_BASE', default='http://your-erp-server.com')
            port = config('DEFAULT_ERP_PORT', default=5000, cast=int)
            logger.warning(f"[Test ERP] No session found, using demo credentials: {user_id}")

        # Test search
        products = product_service.search_products(
            user_id=user_id,
            company_api_base=company_api_base,
            keyword="test",
            port=port
        )

        return JsonResponse({
            'status': 'ERP connection successful',
            'products_found': len(products),
            'sample_products': products[:3] if products else []
        })

    except ERPClientError as e:
        return JsonResponse({
            'status': 'ERP connection failed',
            'error': str(e)
        }, status=500)
