"""
Invoice Lookup Views - Django implementation

Replaces Vue InvoiceLookup.vue component with server-side rendering.
Features:
- Customer autocomplete search
- Invoice search by customer/ship-to ID
- Invoice PDF viewing
- Pagination support
"""

import logging
from typing import Dict, Any
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from services.erp_client import erp_client, ERPClientError

logger = logging.getLogger(__name__)


@ensure_csrf_cookie
@require_http_methods(["GET"])
def invoice_lookup(request):
    """
    Main invoice lookup page - renders the search template
    """
    # Check authentication
    if not request.session.get('customer_logged_in'):
        return redirect('/login/')

    return render(request, 'invoices/invoice_lookup.html')


@require_http_methods(["GET"])
def search_customers(request):
    """
    Search for customers - AJAX endpoint for autocomplete
    """
    try:
        # Get session data
        user_id = request.session.get('customer_user_id') or request.session.get('admin_username')
        company_api_base = request.session.get('customer_company_api_base')
        last_port = request.session.get('customer_last_port', 5000)

        if not user_id or not company_api_base:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

        # Get search keyword
        keyword = request.GET.get('keyword', '').strip()

        if not keyword or len(keyword) < 2:
            return JsonResponse({'success': True, 'results': []})

        # Search customers via ERP
        results = erp_client.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint='/Customers',
            params={'keyword': keyword},
            port=last_port
        )

        # Extract results array
        customers = results.get('results', [])

        return JsonResponse({
            'success': True,
            'results': customers
        })

    except ERPClientError as e:
        logger.error(f"ERP error searching customers: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error searching customers: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def get_customer(request, customer_id):
    """
    Get customer details by ID
    """
    try:
        # Get session data
        user_id = request.session.get('customer_user_id') or request.session.get('admin_username')
        company_api_base = request.session.get('customer_company_api_base')
        last_port = request.session.get('customer_last_port', 5000)

        if not user_id or not company_api_base:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

        # Get customer from ERP
        customer = erp_client.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint=f'/Customers/{customer_id}',
            port=last_port
        )

        return JsonResponse({
            'success': True,
            'customer': customer
        })

    except ERPClientError as e:
        logger.error(f"ERP error fetching customer {customer_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error fetching customer: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def search_invoices(request):
    """
    Search for invoices by ship-to ID
    Returns invoices with pagination
    """
    try:
        # Get session data
        user_id = request.session.get('customer_user_id') or request.session.get('admin_username')
        company_api_base = request.session.get('customer_company_api_base')
        last_port = request.session.get('customer_last_port', 5000)

        if not user_id or not company_api_base:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

        # Get query parameters
        ship_to_id = request.GET.get('shipToId', '').strip()
        start_index = int(request.GET.get('startIndex', 0))
        page_size = int(request.GET.get('pageSize', 25))

        if not ship_to_id:
            return JsonResponse({'success': False, 'error': 'Ship To ID required'}, status=400)

        # Search orders via ERP
        results = erp_client.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint='/SalesOrders',
            params={
                'ShipTo': ship_to_id,
                'OrderStatus': 'Invoice',
                'includeTotalItems': 'true',
                'sort': '-shipDate',
                'startIndex': start_index,
                'pageSize': page_size
            },
            port=last_port
        )

        # Extract and format invoices
        orders = results.get('results', [])
        invoices = []

        for order in orders:
            generations = order.get('generations', [])
            for gen in generations:
                # Filter by ship-to ID
                if str(gen.get('shipToId')) == str(ship_to_id):
                    invoices.append({
                        'shipDate': gen.get('shipDate'),
                        'fullInvoiceID': gen.get('fullInvoiceID') or gen.get('invoiceNumber'),
                        'poNumber': gen.get('poNumber', 'N/A')
                    })

        return JsonResponse({
            'success': True,
            'invoices': invoices,
            'totalItems': results.get('totalItems', len(invoices))
        })

    except ERPClientError as e:
        logger.error(f"ERP error searching invoices: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error searching invoices: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def get_invoice_pdf(request, full_invoice_id):
    """
    Get invoice PDF and return as blob for viewing
    """
    try:
        # Get session data
        user_id = request.session.get('customer_user_id') or request.session.get('admin_username')
        company_api_base = request.session.get('customer_company_api_base')
        last_port = request.session.get('customer_last_port', 5000)

        if not user_id or not company_api_base:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

        # Parse invoice ID: S104950380.001 -> orderId: S104950380, invoiceNumber: "001"
        parts = full_invoice_id.split('.')
        order_id = parts[0]
        # Try keeping as string with leading zeros instead of converting to int
        invoice_number = parts[1] if len(parts) > 1 else "1"

        # Get PDF from ERP
        endpoint = f'/SalesOrders/{order_id}/PrintInvoice'
        params = {'invoiceNumber': invoice_number}

        logger.info(f"Fetching PDF for {full_invoice_id} -> {endpoint}?invoiceNumber={invoice_number}")

        # Get ERP token
        erp_token = erp_client.get_erp_token(user_id)
        if not erp_token:
            raise ERPClientError("No ERP token available")

        # Make request to ERP
        import requests
        url = f"{company_api_base}:{last_port}{endpoint}"
        headers = {
            'Authorization': f'SessionToken {requests.utils.unquote(erp_token)}',
            'Accept': 'application/pdf',
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)

        # Log response details for debugging
        logger.info(f"ERP PDF Response: Status {response.status_code}, Content-Type: {response.headers.get('content-type')}")

        if response.status_code != 200:
            error_body = response.text[:500]  # First 500 chars of error
            logger.error(f"ERP returned {response.status_code}: {error_body}")
            return JsonResponse({
                'success': False,
                'error': f'ERP Error {response.status_code}: {error_body}'
            }, status=500)

        # Return PDF
        return HttpResponse(response.content, content_type='application/pdf')

    except ERPClientError as e:
        logger.error(f"ERP error fetching PDF: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error fetching PDF: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)
