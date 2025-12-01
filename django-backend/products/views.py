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

def product_search_page(request):
    """Product search page - Search products and view JSON data"""
    return render(request, 'products/search_tailwind.html')

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

        # Check if it's a 404 (product not found)
        if '404' in error_message or 'not found' in error_message.lower():
            logger.warning(
                f"[Product Get] 404 Not Found - Product ID: {product_id} | "
                f"User: {user_id} | Port: {port} | "
                f"Possible causes: product deleted, wrong ID type (PDW vs Eclipse), "
                f"or branch access restriction"
            )
            return JsonResponse({
                'id': product_id,
                'error': 'Product not found',
                'description': 'Not found',
                'upc': 'N/A',
                'priceLineId': 'N/A',
                'buyLineId': 'N/A'
            }, status=200)  # Return 200 with error fields so frontend doesn't break

        logger.error(f"ERP get product failed for ID '{product_id}': {e}")

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

@require_product('eclipse')
def warehouse_dashboard_page(request):
    """Warehouse dashboard - View invoices with printStatus 'Q' (awaiting pickup)"""
    return render(request, 'products/warehouse_dashboard.html')

def warehouse_api_branches(request):
      """API endpoint to get user's accessible branches from ERP"""
      try:
          # Check if user is authenticated
          if request.session.get('customer_logged_in'):
              user_id = request.session.get('customer_user_id')
              erp_username = request.session.get('customer_erp_username')
              company_api_base = request.session.get('customer_company_api_base')
              port = int(request.session.get('customer_last_port', 5000))
          elif request.session.get('admin_logged_in'):
              user_id = request.session.get('admin_user_id')
              erp_username = request.session.get('admin_username')
              company_api_base = request.session.get('admin_company_api_base')
              port = int(request.session.get('admin_port', 5000))
          else:
              return JsonResponse({'error': 'Not authenticated'}, status=401)

          if not all([user_id, company_api_base, erp_username]):
              return JsonResponse({'error': 'Missing session data'}, status=400)

          from services.erp_client import erp_client

          # Call ERP /Users/{erp_username} to get user data with accessible branches
          user_data = erp_client.make_erp_request(
              user_id=user_id,
              company_api_base=company_api_base,
              port=port,
              method='GET',
              endpoint=f'/Users/{erp_username}'
          )

          # Extract branches
          accessible_branches = user_data.get('accessibleBranches', [])
          branch_ids = [b.get('branchId') for b in accessible_branches if isinstance(b, dict) and b.get('branchId')]

          logger.info(f"[Warehouse API] Found {len(branch_ids)} branches for {erp_username}: {branch_ids}")

          return JsonResponse({'branches': branch_ids})

      except Exception as e:
          logger.error(f"[Warehouse API] Error getting branches: {e}")
          import traceback
          logger.error(traceback.format_exc())
          return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def warehouse_api_orders(request):
    """
    API endpoint to get warehouse orders with printStatus='Q'

    Now queries MongoDB (populated by email CSV processing) instead of direct ERP API calls
    for faster, more reliable results.
    """
    try:
        # Check if user is authenticated
        if request.session.get('customer_logged_in'):
            user_id = request.session.get('customer_user_id')
            company_code = request.session.get('customer_company_code')
            company_api_base = request.session.get('customer_company_api_base')
            port = int(request.session.get('customer_last_port', 5000))
        elif request.session.get('admin_logged_in'):
            user_id = request.session.get('admin_user_id')
            company_code = request.session.get('admin_company_code')
            company_api_base = request.session.get('admin_company_api_base')
            port = int(request.session.get('admin_port', 5000))
        else:
            return JsonResponse({'error': 'Not authenticated'}, status=401)

        if not all([user_id, company_code]):
            return JsonResponse({'error': 'Missing session data'}, status=400)

        # Get request parameters
        if request.method == 'POST':
            data = json.loads(request.body)
        else:
            data = request.GET

        branch = data.get('branch')
        ship_via_keywords = data.get('shipViaKeywords', '')

        if not branch:
            return JsonResponse({'error': 'Branch is required'}, status=400)

        logger.info(f"[Warehouse API] Fetching orders from MongoDB for company: {company_code}, branch: {branch}")

        # Connect to MongoDB
        from pymongo import MongoClient
        mongo_uri = config('MONGO_URI')
        db_name = config('DB_NAME', default='emp54')

        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db['warehouse_invoices']

        # Build MongoDB query
        query = {
            'companyCode': company_code,
            'branch': branch,
            'printStatus': 'Q'  # Should already be filtered in CSV, but double-check
        }

        # Query MongoDB
        mongo_orders = list(collection.find(query))
        logger.info(f"[Warehouse API] Found {len(mongo_orders)} orders from MongoDB")

        # Process and filter orders
        processed_orders = []
        keywords = [k.strip().upper() for k in ship_via_keywords.split(',') if k.strip()]

        # Import ERP client for status lookups
        from services.erp_client import erp_client

        for order in mongo_orders:
            ship_via = order.get('shipVia', '')

            # Filter by ship via keywords if provided
            if keywords:
                if not any(keyword in ship_via.upper() for keyword in keywords):
                    continue

            full_invoice_id = order.get('fullInvoiceID')

            # Skip orders with null/missing fullInvoiceID
            if not full_invoice_id:
                logger.debug(f"[Warehouse API] Skipping order with null fullInvoiceID")
                continue

            # Extract order number and generation ID from fullInvoiceID
            # Format: S105418530.001 → order=S105418530, generation=1
            try:
                parts = full_invoice_id.split('.')
                if len(parts) != 2:
                    logger.warning(f'[Warehouse API] Invalid fullInvoiceID format: {full_invoice_id}')
                    continue

                order_number = parts[0]
                generation_id = int(parts[1])
                padded_gen_id = str(generation_id).zfill(4)
                api_id = f'{order_number}.{padded_gen_id}'

            except Exception as parse_err:
                logger.warning(f'[Warehouse API] Could not parse fullInvoiceID {full_invoice_id}: {parse_err}')
                continue

            # Fetch shipDate and custName from SalesOrders API (lightweight single-order lookup)
            ship_date = ''
            ship_to_name = ''
            po_number = ''
            balance_due = 0

            try:
                order_data = erp_client.make_erp_request(
                    user_id=user_id,
                    company_api_base=company_api_base,
                    port=port,
                    method='GET',
                    endpoint=f'/SalesOrders/{order_number}'
                )

                # Get the specific generation
                generations = order_data.get('generations', [])
                matching_gen = next((g for g in generations if g.get('generationId') == generation_id), None)

                if matching_gen:
                    ship_date = matching_gen.get('shipDate', '')
                    ship_to_name = matching_gen.get('shipToName', '')
                    po_number = matching_gen.get('poNumber', '')
                    balance_due_obj = matching_gen.get('balanceDue', {})
                    balance_due = balance_due_obj.get('value', 0) if isinstance(balance_due_obj, dict) else balance_due_obj

            except Exception as order_err:
                # Log but don't fail - we can still show the invoice without these fields
                if '404' not in str(order_err):
                    logger.warning(f'[Warehouse API] Could not fetch order details for {full_invoice_id}: {order_err}')

            # Fetch status from PRINT.REVIEW API
            status = ''
            try:
                print_review_data = erp_client.make_erp_request(
                    user_id=user_id,
                    company_api_base=company_api_base,
                    port=port,
                    method='GET',
                    endpoint=f'/UserDefined/PRINT.REVIEW?id={api_id}'
                )
                status = print_review_data.get('STATUS', '')
            except Exception as status_err:
                # Ignore 404s (normal for invoices without PRINT.REVIEW records)
                if '404' not in str(status_err):
                    logger.warning(f'[Warehouse API] Could not fetch status for {full_invoice_id}: {status_err}')

            # Build order object
            processed_orders.append({
                'shipDate': ship_date,
                'fullInvoiceID': full_invoice_id,
                'shipToName': ship_to_name,
                'poNumber': po_number,
                'shipVia': ship_via,
                'termsCode': '',  # Not needed, omit for now
                'balanceDue': balance_due,
                'status': status
            })

        # Sort by ship date (newest first)
        processed_orders.sort(key=lambda x: x.get('shipDate', ''), reverse=True)

        logger.info(f"[Warehouse API] Returning {len(processed_orders)} filtered orders")

        return JsonResponse({'orders': processed_orders})

    except Exception as e:
        logger.error(f"[Warehouse API] Error fetching orders: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
