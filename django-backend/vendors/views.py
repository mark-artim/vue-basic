"""
Vendor Management Views - Django implementation

Replaces Vue VendorAdd.vue component with server-side rendering.
Supports two workflows:
1. Add Ship-From for Existing Pay-To Vendor
2. Add New Pay-To Only Vendor
"""

import json
import re
import logging
from typing import List, Dict, Any
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from services.erp_client import erp_client, ERPClientError

logger = logging.getLogger(__name__)

# Hard-coded vendor options (from Vue implementation)
VENDOR_OPTIONS = [
    {
        'code': 'BBS',
        'name': 'Benoist',
        'homeBranch': 'ILMV',
        'homeTerritory': 'TCBBS'
    },
    {
        'code': 'CSC',
        'name': 'Coastal',
        'homeBranch': 'TNKN',
        'homeTerritory': 'TCCSC'
    },
    {
        'code': 'ESC',
        'name': "Ed's Central",
        'homeBranch': 'TNNA',
        'homeTerritory': 'TCESC'
    },
    {
        'code': 'ESE',
        'name': "Ed's East",
        'homeBranch': 'TNCH',
        'homeTerritory': 'TCESE'
    },
    {
        'code': 'ESW',
        'name': "Ed's West",
        'homeBranch': 'ARLR',
        'homeTerritory': 'TCESW'
    },
    {
        'code': 'NCS',
        'name': 'NuComfort',
        'homeBranch': 'ILCS',
        'homeTerritory': 'TCNCS'
    },
    {
        'code': 'WSC',
        'name': 'Wittichen',
        'homeBranch': '1',
        'homeTerritory': 'TCWSC'
    }
]

# Valid vendor types (from validators.js)
VALID_VENDOR_TYPES = [
    'EXP', 'EXP:EMPL', 'EXP:UTY', 'INV', 'A-F', 'G-O', 'P-Z',
    'LBMX:A-F', 'LBMX:G-O', 'LBMX:N-Z', 'LBMX:NEUCO', 'PC', 'RHEEM', 'EXP-AUTODR'
]


def parse_emails(email_text: str) -> List[Dict[str, str]]:
    """
    Parse multi-line email text into list of email objects.
    Returns format: [{ "address": "email@example.com" }]
    """
    if not email_text:
        return []
    return [
        {'address': email.strip()}
        for email in email_text.split('\n')
        if email.strip()
    ]


def parse_phones(phone_text: str) -> List[Dict[str, str]]:
    """
    Parse multi-line phone text into list of phone objects.
    Format: "555-1234 (MAIN)"
    Matches Vue implementation.
    """
    if not phone_text:
        return []

    phones = []
    phone_pattern = re.compile(r'^(.+?)\s*\((.*?)\)$')

    for line in phone_text.split('\n'):
        line = line.strip()
        if not line:
            continue

        match = phone_pattern.match(line)
        if match:
            phones.append({
                'number': match.group(1).strip(),
                'description': match.group(2).strip()
            })
        else:
            # If no description, use the whole line as number
            phones.append({
                'number': line,
                'description': ''
            })

    return phones


@ensure_csrf_cookie
@require_http_methods(["GET"])
def vendor_add(request):
    """
    Main vendor add page - renders the form template
    """
    # Check authentication
    if not request.session.get('customer_logged_in'):
        return redirect('/customer-auth/login/')

    # DEBUG: Log session data including ERP token
    logger.info("=" * 80)
    logger.info("VENDOR ADD PAGE - SESSION DATA DUMP")
    logger.info("=" * 80)
    for key, value in request.session.items():
        # Mask sensitive data partially for security
        if 'token' in key.lower() or 'password' in key.lower():
            logger.info(f"  {key}: {value}")
        else:
            logger.info(f"  {key}: {value}")
    logger.info("=" * 80)

    context = {
        'vendor_options': VENDOR_OPTIONS,
        'valid_vendor_types': VALID_VENDOR_TYPES
    }

    return render(request, 'vendors/vendor_add.html', context)


@require_http_methods(["GET"])
def search_payto_vendors(request):
    """
    Search for existing pay-to vendors
    AJAX endpoint for autocomplete
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

        if not keyword:
            return JsonResponse({'success': True, 'vendors': []})

        # Search vendors via ERP
        results = erp_client.search_vendors(
            user_id=user_id,
            company_api_base=company_api_base,
            keyword=keyword,
            port=last_port
        )

        # Filter to only pay-to vendors
        payto_vendors = [v for v in results.get('results', []) if v.get('isPayTo')]

        return JsonResponse({
            'success': True,
            'vendors': payto_vendors
        })

    except ERPClientError as e:
        logger.error(f"ERP error searching vendors: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error searching vendors: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def get_shipfrom_vendors(request, payto_id):
    """
    Get existing ship-from vendors for a pay-to vendor
    AJAX endpoint
    """
    try:
        # Get session data
        user_id = request.session.get('customer_user_id') or request.session.get('admin_username')
        company_api_base = request.session.get('customer_company_api_base')
        last_port = request.session.get('customer_last_port', 5000)

        if not user_id or not company_api_base:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

        # Get vendor by ID to access shipFromLists
        vendor = erp_client.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint=f'/Vendors/{payto_id}',
            port=last_port
        )

        # Extract ship-from IDs
        ship_from_ids = [item.get('shipFromId') for item in vendor.get('shipFromLists', []) if item.get('shipFromId')]

        # Fetch each ship-from vendor
        ship_from_vendors = []
        for sf_id in ship_from_ids:
            try:
                sf_vendor = erp_client.make_erp_request(
                    user_id=user_id,
                    company_api_base=company_api_base,
                    method='GET',
                    endpoint=f'/Vendors/{sf_id}',
                    port=last_port
                )
                ship_from_vendors.append(sf_vendor)
            except ERPClientError as e:
                logger.warning(f"Could not fetch ship-from vendor {sf_id}: {e}")
                continue

        # Sort alphabetically by nameIndex
        ship_from_vendors.sort(key=lambda v: v.get('nameIndex', '').lower())

        return JsonResponse({
            'success': True,
            'vendors': ship_from_vendors
        })

    except ERPClientError as e:
        logger.error(f"ERP error fetching ship-from vendors: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error fetching ship-from vendors: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)


@require_http_methods(["POST"])
def create_vendors(request):
    """
    Create one or more vendors
    Handles both ship-from and pay-to vendor creation
    """
    try:
        # Get session data
        user_id = request.session.get('customer_user_id') or request.session.get('admin_username')
        company_api_base = request.session.get('customer_company_api_base')
        last_port = request.session.get('customer_last_port', 5000)

        if not user_id or not company_api_base:
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)

        # Parse request body
        data = json.loads(request.body)
        vendors = data.get('vendors', [])

        if not vendors:
            return JsonResponse({'success': False, 'error': 'No vendors provided'}, status=400)

        created_vendors = []
        errors = []

        # Process each vendor
        for vendor_data in vendors:
            try:
                # Parse emails and phones (handle both string and array formats)
                emails_data = vendor_data.get('emails', '')
                phones_data = vendor_data.get('phones', '')

                # If emails is already an array (from new frontend), use it directly
                # Otherwise parse from string (backward compatibility)
                if isinstance(emails_data, list):
                    emails = emails_data
                else:
                    emails = parse_emails(emails_data)

                # Same for phones
                if isinstance(phones_data, list):
                    phones = phones_data
                else:
                    phones = parse_phones(phones_data)

                # Build vendor object for ERP
                vendor_payload = {
                    'name': vendor_data.get('name', '').upper(),
                    'nameIndex': vendor_data.get('nameIndex', '').upper(),
                    'addressLine1': vendor_data.get('addressLine1', ''),
                    'addressLine2': vendor_data.get('addressLine2', ''),
                    'city': vendor_data.get('city', ''),
                    'state': vendor_data.get('state', ''),
                    'postalCode': vendor_data.get('postalCode', ''),
                    'countryCode': vendor_data.get('countryCode', 'US'),
                    'sortBy': vendor_data.get('sortBy', vendor_data.get('name', '')[:12].upper()),
                    'defaultShipVia': vendor_data.get('defaultShipVia', ''),
                    'freight': vendor_data.get('freight', ''),
                    'defaultTerms': vendor_data.get('defaultTerms', ''),
                    'backOrderDays': vendor_data.get('backOrderDays', 7),
                    'emails': emails,
                    'phones': phones,
                    'type': vendor_data.get('type', ''),
                    'isPayTo': vendor_data.get('isPayTo', False),
                    'isShipFrom': vendor_data.get('isShipFrom', False),
                    'isFreightVendor': vendor_data.get('isFreightVendor', False),
                    'isManufacturer': vendor_data.get('isManufacturer', False),
                }

                # Add ship-from specific fields if applicable
                if vendor_data.get('isShipFrom'):
                    vendor_payload['homeBranch'] = vendor_data.get('homeBranch', '')
                    vendor_payload['homeTerritory'] = vendor_data.get('homeTerritory', '')
                    vendor_payload['payToId'] = vendor_data.get('payToId', '')

                # Create vendor via ERP
                result = erp_client.create_entity(
                    user_id=user_id,
                    company_api_base=company_api_base,
                    endpoint='/Vendors',
                    data=vendor_payload,
                    port=last_port
                )

                created_vendors.append(result)

            except ERPClientError as e:
                logger.error(f"ERP error creating vendor: {e}")
                errors.append({
                    'vendor_name': vendor_data.get('name', 'Unknown'),
                    'error': str(e)
                })
            except Exception as e:
                logger.error(f"Error creating vendor: {e}")
                errors.append({
                    'vendor_name': vendor_data.get('name', 'Unknown'),
                    'error': str(e)
                })

        # Return results
        if errors:
            return JsonResponse({
                'success': False,
                'created': created_vendors,
                'errors': errors
            }, status=207)  # Multi-status

        return JsonResponse({
            'success': True,
            'created': created_vendors,
            'message': f'Successfully created {len(created_vendors)} vendor(s)'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in create_vendors: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)
