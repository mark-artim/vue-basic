from django.http import JsonResponse
from services.mongodb_service import mongodb_service
import logging

logger = logging.getLogger(__name__)

def warehouse_api_branches_debug(request):
    """Debug version of warehouse_api_branches with full logging"""
    debug_info = {}

    try:
        # Check session data
        debug_info['customer_logged_in'] = request.session.get('customer_logged_in', False)
        debug_info['admin_logged_in'] = request.session.get('admin_logged_in', False)

        # Check if user is authenticated
        if request.session.get('customer_logged_in'):
            erp_username = request.session.get('customer_erp_username')
            debug_info['auth_type'] = 'customer'
            debug_info['erp_username'] = erp_username
        elif request.session.get('admin_logged_in'):
            erp_username = request.session.get('admin_username')
            debug_info['auth_type'] = 'admin'
            debug_info['admin_username'] = erp_username
        else:
            debug_info['error'] = 'Not authenticated'
            return JsonResponse(debug_info, status=401)

        if not erp_username:
            debug_info['error'] = 'No username in session'
            return JsonResponse(debug_info, status=400)

        # Find user by erpUserName
        user = mongodb_service.db.users.find_one({'erpUserName': erp_username.upper()})
        if not user:
            user = mongodb_service.db.users.find_one({'erpUserName': erp_username.lower()})

        if not user:
            # Try finding by email or other fields
            user = mongodb_service.db.users.find_one({'email': erp_username})
            debug_info['found_by_email'] = user is not None

        if not user:
            debug_info['error'] = 'User not found in MongoDB'
            debug_info['searched_for'] = erp_username
            return JsonResponse(debug_info, status=404)

        # Show user data
        debug_info['user_email'] = user.get('email')
        debug_info['user_id'] = str(user.get('_id'))
        debug_info['user_type'] = user.get('userType')

        # Extract accessible branches
        accessible_branches = user.get('accessibleBranches', [])
        debug_info['accessible_branches_count'] = len(accessible_branches)
        debug_info['accessible_branches'] = accessible_branches

        branch_ids = [b.get('branchId') for b in accessible_branches if b.get('branchId')]
        debug_info['extracted_branch_ids'] = branch_ids

        return JsonResponse(debug_info)

    except Exception as e:
        debug_info['exception'] = str(e)
        import traceback
        debug_info['traceback'] = traceback.format_exc()
        return JsonResponse(debug_info, status=500)
