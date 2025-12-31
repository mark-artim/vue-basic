"""
Branch Transfer Analysis Views

Client-side CSV processing tool for analyzing branch-to-branch transfers by buyline.
No server-side processing - all analysis happens in the browser for speed and privacy.
"""

import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from services.erp_client import erp_client, ERPClientError

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def branch_transfer_analysis(request):
    """
    Main branch transfer analysis page
    Renders upload interface and analysis tools
    """
    if not request.session.get('customer_logged_in'):
        return redirect('/login/')

    return render(request, 'branch_analysis/transfer_analysis.html')


@require_http_methods(["GET"])
def get_branch(request, branch_id):
    """
    Proxy to Eclipse GET /Branches/{id} endpoint
    Returns branch data including branchEntityId
    """
    try:
        # Get session data
        user_id = request.session.get('customer_user_id') or request.session.get('admin_username')
        company_api_base = request.session.get('customer_company_api_base')
        last_port = request.session.get('customer_last_port', 5000)

        if not user_id or not company_api_base:
            return JsonResponse({'error': 'Not authenticated'}, status=401)

        # Get branch from ERP
        branch_data = erp_client.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint=f'/Branches/{branch_id}',
            port=last_port
        )

        return JsonResponse(branch_data, safe=False)

    except ERPClientError as e:
        logger.error(f"ERP error fetching branch {branch_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error fetching branch: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def get_customer(request, customer_id):
    """
    Proxy to Eclipse GET /Customers/{id} endpoint
    Returns customer data including address fields
    """
    try:
        # Get session data
        user_id = request.session.get('customer_user_id') or request.session.get('admin_username')
        company_api_base = request.session.get('customer_company_api_base')
        last_port = request.session.get('customer_last_port', 5000)

        if not user_id or not company_api_base:
            return JsonResponse({'error': 'Not authenticated'}, status=401)

        # Get customer from ERP
        customer_data = erp_client.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint=f'/Customers/{customer_id}',
            port=last_port
        )

        return JsonResponse(customer_data, safe=False)

    except ERPClientError as e:
        logger.error(f"ERP error fetching customer {customer_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error fetching customer: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def geocode_address(request):
    """
    Proxy to Nominatim geocoding service (fixes CORS issues)
    Query param: address
    Returns: {lat: float, lng: float} or {error: string}
    """
    try:
        address = request.GET.get('address', '').strip()
        if not address:
            return JsonResponse({'error': 'Address parameter required'}, status=400)

        # Call Nominatim API (server-side, no CORS issues)
        import requests
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'format': 'json',
            'q': address,
            'limit': 1
        }
        headers = {
            'User-Agent': 'BranchTransferAnalysis/1.0 (Django Backend)'
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error(f"Nominatim error: {response.status_code}")
            return JsonResponse({'error': f'Geocoding service error: {response.status_code}'}, status=500)

        data = response.json()

        if len(data) > 0:
            return JsonResponse({
                'lat': float(data[0]['lat']),
                'lng': float(data[0]['lon'])
            })
        else:
            return JsonResponse({'error': 'No results found for address'}, status=404)

    except requests.RequestException as e:
        logger.error(f"Geocoding request error: {e}")
        return JsonResponse({'error': 'Geocoding service unavailable'}, status=503)
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
