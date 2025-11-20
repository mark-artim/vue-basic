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
