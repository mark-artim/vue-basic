"""
Core views for common functionality across the application
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from services.mongodb_service import mongodb_service
import json
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def switch_port(request):
    """
    API endpoint to switch the ERP port - updates both session AND MongoDB
    This ensures the next login uses the selected port
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        port = data.get('port')

        if not port:
            return JsonResponse({'error': 'Port is required'}, status=400)

        # Validate port
        valid_ports = ['5000', '5001', '5002', '5003', '5004', '5005']
        if port not in valid_ports:
            return JsonResponse({'error': f'Invalid port. Must be one of: {", ".join(valid_ports)}'}, status=400)

        # Update based on user type
        if request.session.get('customer_logged_in'):
            customer_email = request.session.get('customer_email')

            # Update session
            request.session['customer_last_port'] = port

            # Update MongoDB so next login uses this port
            user = mongodb_service.find_user_by_email(customer_email)
            if user:
                mongodb_service.update_user_port(user['_id'], port)
                logger.info(f"Customer user {customer_email} switched to port {port} (updated MongoDB)")
            else:
                logger.warning(f"Could not find user {customer_email} to update port in MongoDB")

        elif request.session.get('admin_logged_in'):
            request.session['admin_port'] = port
            logger.info(f"Admin user switched to port {port}")
        else:
            return JsonResponse({'error': 'User not logged in'}, status=401)

        return JsonResponse({
            'success': True,
            'port': port,
            'message': f'Successfully switched to port {port}'
        })

    except Exception as e:
        logger.error(f"Error switching port: {e}")
        return JsonResponse({
            'error': 'Failed to switch port',
            'details': str(e)
        }, status=500)


@csrf_exempt
def session_debug(request):
    """
    API endpoint to get ERP session debugging information
    Calls GET /Sessions/{id} to retrieve session details
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Check if user is logged in
        if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
            return JsonResponse({'error': 'User not logged in'}, status=401)

        # Get session data based on user type
        if request.session.get('customer_logged_in'):
            user_id = request.session.get('customer_user_id')
            company_api_base = request.session.get('customer_company_api_base')
            last_port = request.session.get('customer_last_port', 5000)
            session_id = request.session.get('customer_erp_session_id')
        else:  # admin
            # Admins don't use ERP sessions
            return JsonResponse({
                'error': 'Session debugging only available for customer users',
                'user_type': 'admin'
            }, status=400)

        if not session_id:
            return JsonResponse({
                'error': 'No ERP session found',
                'details': 'User does not have an active ERP session'
            }, status=404)

        # Import here to avoid circular imports
        from services.erp_client import erp_client

        # Call ERP GET /Sessions/{id}
        session_data = erp_client.make_erp_request(
            user_id=user_id,
            company_api_base=company_api_base,
            method='GET',
            endpoint=f'/Sessions/{session_id}',
            port=last_port
        )

        # Add Django session metadata for debugging
        django_session_info = {
            'django_session_key': request.session.session_key,
            'customer_email': request.session.get('customer_email'),
            'customer_name': request.session.get('customer_name'),
            'customer_company_code': request.session.get('customer_company_code'),
            'customer_last_port': last_port,
        }

        return JsonResponse({
            'success': True,
            'erp_session': session_data,
            'django_session': django_session_info
        })

    except Exception as e:
        logger.error(f"Error fetching session debug info: {e}")
        return JsonResponse({
            'error': 'Failed to fetch session information',
            'details': str(e)
        }, status=500)
