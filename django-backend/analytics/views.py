"""
PO Analytics Views

Handles CSV import, analytics queries, and reporting.
"""

import csv
import io
import uuid
import threading
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from services.analytics_mongodb_service import analytics_mongodb
import logging

logger = logging.getLogger(__name__)


def process_csv_import(file_data, skip_rows, overwrite_mode, import_batch_id, company_code, user_email, filename):
    """
    Background worker function to process CSV import with progress updates.
    Uses bulk insert optimization for 10-50x faster imports.
    """
    BATCH_SIZE = 1000  # Insert 1000 records at a time

    try:
        lines = file_data.splitlines()

        # Skip the specified number of rows before headers
        if skip_rows > 0:
            lines = lines[skip_rows:]

        csv_reader = csv.DictReader(lines)

        imported_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        total_rows = 0

        # First pass: count total rows
        rows_list = list(csv_reader)
        total_rows = len(rows_list)

        # Update log with total
        analytics_mongodb.update_import_log(import_batch_id, {
            'total_rows': total_rows,
            'status': 'processing'
        })

        # Batch processing
        batch = []
        batch_po_numbers = []

        for row_num, row in enumerate(rows_list, start=2):
            try:
                # Parse and validate data
                po_payto_id = row.get('PO_PAYTO_ID', '').strip()
                po_payto_name = row.get('PO_PAYTO_NAME', '').strip()
                po_company = row.get('PO_COMPANY', '').strip()
                po_branch = row.get('PO_BRANCH', '').strip()
                po_number = row.get('PO_NUMBER', '').strip()
                order_total_str = row.get('ORDER_TOTAL', '').strip()
                order_date_str = row.get('ORDER_DATE', '').strip()

                # Validate required fields
                if not all([po_payto_id, po_payto_name, po_company, po_branch, po_number, order_total_str, order_date_str]):
                    error_count += 1
                    errors.append(f"Row {row_num}: Missing required fields")
                    continue

                # Parse order total
                try:
                    order_total = Decimal(order_total_str.replace(',', ''))
                except (InvalidOperation, ValueError):
                    error_count += 1
                    errors.append(f"Row {row_num}: Invalid order total: {order_total_str}")
                    continue

                # Parse order date (format: MM/DD/YYYY)
                try:
                    order_date = datetime.strptime(order_date_str, '%m/%d/%Y').date()
                except ValueError:
                    error_count += 1
                    errors.append(f"Row {row_num}: Invalid date format: {order_date_str} (expected MM/DD/YYYY)")
                    continue

                # Add to batch
                po_doc = {
                    'po_payto_id': po_payto_id,
                    'po_payto_name': po_payto_name,
                    'po_company': po_company,
                    'po_branch': po_branch,
                    'po_number': po_number,
                    'order_total': float(order_total),
                    'order_date': datetime.combine(order_date, datetime.min.time()),
                    'company_code': company_code,
                    'import_batch_id': import_batch_id,
                    'imported_by_email': user_email,
                    'source_file': filename,
                    'imported_at': datetime.now()
                }
                batch.append(po_doc)
                batch_po_numbers.append(po_number)

                # Process batch when it reaches BATCH_SIZE or end of file
                if len(batch) >= BATCH_SIZE or row_num == len(rows_list) + 1:
                    # Handle duplicates
                    if overwrite_mode:
                        # Delete all existing POs in this batch
                        analytics_mongodb.purchase_orders.delete_many({
                            'po_number': {'$in': batch_po_numbers},
                            'company_code': company_code
                        })
                        # Insert all records in batch
                        inserted_count = analytics_mongodb.insert_many_purchase_orders(batch)
                        imported_count += inserted_count
                    else:
                        # Find existing PO numbers in batch
                        existing_pos = analytics_mongodb.purchase_orders.find(
                            {
                                'po_number': {'$in': batch_po_numbers},
                                'company_code': company_code
                            },
                            {'po_number': 1}
                        )
                        existing_po_numbers = {po['po_number'] for po in existing_pos}

                        # Filter out existing records
                        new_records = [doc for doc in batch if doc['po_number'] not in existing_po_numbers]
                        skipped_count += len(batch) - len(new_records)

                        # Bulk insert only new records
                        if new_records:
                            inserted_count = analytics_mongodb.insert_many_purchase_orders(new_records)
                            imported_count += inserted_count

                    # Update progress
                    analytics_mongodb.update_import_log(import_batch_id, {
                        'imported_rows': imported_count,
                        'skipped_rows': skipped_count,
                        'error_rows': error_count
                    })

                    # Clear batch
                    batch = []
                    batch_po_numbers = []

            except Exception as e:
                error_count += 1
                errors.append(f"Row {row_num}: {str(e)}")

        # Final update
        analytics_mongodb.update_import_log(import_batch_id, {
            'imported_rows': imported_count,
            'skipped_rows': skipped_count,
            'error_rows': error_count,
            'status': 'completed' if error_count == 0 else 'completed_with_errors',
            'error_message': '\n'.join(errors[:10]) if errors else None
        })

        logger.info(f"Import {import_batch_id} completed: {imported_count} imported, {skipped_count} skipped, {error_count} errors")

    except Exception as e:
        logger.error(f"Import {import_batch_id} failed: {str(e)}")
        analytics_mongodb.update_import_log(import_batch_id, {
            'status': 'failed',
            'error_message': str(e)
        })


def po_insights(request):
    """
    Main PO Analytics page.
    Displays filters, charts, and analytics interface.
    """
    # Check authentication - redirect to login if not authenticated
    if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
        return redirect('/login/')

    # Get user session data
    user_email = request.session.get('customer_email') or request.session.get('admin_username', 'unknown')
    company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

    context = {
        'user_email': user_email,
        'company_code': company_code,
    }

    return render(request, 'analytics/po_insights.html', context)


@require_http_methods(["POST"])
def import_csv(request):
    """
    Import PO data from CSV file.
    Accepts CSV with columns: PO_PAYTO_ID, PO_PAYTO_NAME, PO_COMPANY, PO_BRANCH,
                               PO_NUMBER, ORDER_TOTAL, ORDER_DATE
    """
    try:
        # Check authentication
        if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

        # Get user session data
        user_email = request.session.get('customer_email') or request.session.get('admin_username', 'unknown')
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Get uploaded file
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)

        uploaded_file = request.FILES['file']
        filename = uploaded_file.name

        # Validate CSV file
        if not filename.endswith('.csv'):
            return JsonResponse({'success': False, 'error': 'Only CSV files are supported'}, status=400)

        # Get parameters
        skip_rows = int(request.POST.get('skip_rows', 0))
        overwrite_mode = request.POST.get('overwrite_mode', 'false').lower() == 'true'

        # Generate unique batch ID for this import
        import_batch_id = str(uuid.uuid4())

        # Create import log in MongoDB
        analytics_mongodb.create_import_log({
            'import_batch_id': import_batch_id,
            'filename': filename,
            'file_key': f"companies/{company_code}/po-imports/{filename}",
            'company_code': company_code,
            'imported_by_email': user_email,
            'status': 'processing',
            'total_rows': 0,
            'imported_rows': 0,
            'skipped_rows': 0,
            'error_rows': 0,
            'imported_at': datetime.now()
        })

        # Read CSV into memory
        file_data = uploaded_file.read().decode('utf-8')

        # Start background thread for processing
        thread = threading.Thread(
            target=process_csv_import,
            args=(file_data, skip_rows, overwrite_mode, import_batch_id, company_code, user_email, filename)
        )
        thread.daemon = True
        thread.start()

        # Return immediately with batch ID - frontend will poll for progress
        return JsonResponse({
            'success': True,
            'import_batch_id': import_batch_id,
            'message': 'Import started in background. Refresh to see progress.'
        })

    except Exception as e:
        # Update import log if it exists
        if 'import_batch_id' in locals():
            analytics_mongodb.update_import_log(import_batch_id, {
                'status': 'failed',
                'error_message': str(e)
            })

        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def import_status(request, batch_id):
    """
    Get current status of an import operation.
    Used by frontend to poll for progress during background imports.
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Get import log from MongoDB
        import_log = analytics_mongodb.get_import_log(batch_id)

        if not import_log:
            return JsonResponse({'success': False, 'error': 'Import not found'}, status=404)

        # Verify batch belongs to this company
        if import_log.get('company_code') != company_code:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

        # Convert MongoDB _id and datetime to JSON-serializable formats
        if '_id' in import_log:
            import_log['_id'] = str(import_log['_id'])
        if 'imported_at' in import_log and import_log['imported_at']:
            import_log['imported_at'] = import_log['imported_at'].isoformat()

        return JsonResponse({
            'success': True,
            'import': import_log
        })

    except Exception as e:
        logger.error(f"Error getting import status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def query_vendors(request):
    """
    Query PO data by vendor.
    GET params: vendor_name (optional), start_date, end_date, company, branch
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Build MongoDB filters
        mongo_filters = {}

        # Vendor filter
        vendor_name = request.GET.get('vendor_name')
        if vendor_name:
            mongo_filters['po_payto_name'] = {'$regex': vendor_name, '$options': 'i'}

        # Date range filter
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date or end_date:
            mongo_filters['order_date'] = {}
            if start_date:
                mongo_filters['order_date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                mongo_filters['order_date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')

        # Company filter
        po_company = request.GET.get('company')
        if po_company:
            mongo_filters['po_company'] = po_company

        # Branch filter
        branch = request.GET.get('branch')
        if branch:
            mongo_filters['po_branch'] = branch

        # Use MongoDB aggregation
        vendors = analytics_mongodb.aggregate_vendors(company_code, mongo_filters)

        return JsonResponse({'success': True, 'vendors': vendors})

    except Exception as e:
        logger.error(f"Error querying vendors: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def query_branches(request):
    """
    Query PO data by branch.
    GET params: branch (optional), start_date, end_date, vendor_name
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Build MongoDB filters
        mongo_filters = {}

        # Branch filter
        branch = request.GET.get('branch')
        if branch:
            mongo_filters['po_branch'] = branch

        # Date range filter
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date or end_date:
            mongo_filters['order_date'] = {}
            if start_date:
                mongo_filters['order_date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                mongo_filters['order_date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')

        # Vendor filter
        vendor_name = request.GET.get('vendor_name')
        if vendor_name:
            mongo_filters['po_payto_name'] = {'$regex': vendor_name, '$options': 'i'}

        # Use MongoDB aggregation
        branches = analytics_mongodb.aggregate_branches(company_code, mongo_filters)

        return JsonResponse({'success': True, 'branches': branches})

    except Exception as e:
        logger.error(f"Error querying branches: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def query_companies(request):
    """
    Query PO data by company.
    GET params: company (optional), start_date, end_date, vendor_name, branch
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Build MongoDB filters
        mongo_filters = {}

        # Company filter
        po_company = request.GET.get('company')
        if po_company:
            mongo_filters['po_company'] = po_company

        # Date range filter
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date or end_date:
            mongo_filters['order_date'] = {}
            if start_date:
                mongo_filters['order_date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                mongo_filters['order_date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')

        # Vendor filter
        vendor_name = request.GET.get('vendor_name')
        if vendor_name:
            mongo_filters['po_payto_name'] = {'$regex': vendor_name, '$options': 'i'}

        # Branch filter
        branch = request.GET.get('branch')
        if branch:
            mongo_filters['po_branch'] = branch

        # Use MongoDB aggregation
        companies = analytics_mongodb.aggregate_companies(company_code, mongo_filters)

        return JsonResponse({'success': True, 'companies': companies})

    except Exception as e:
        logger.error(f"Error querying companies: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def vendor_company_breakdown(request, vendor_name):
    """
    Get company breakdown for a specific vendor.
    Shows which companies buy from this vendor and how much.
    GET params: start_date, end_date, branch
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Build MongoDB filters
        mongo_filters = {'po_payto_name': vendor_name}

        # Date range filter
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date or end_date:
            mongo_filters['order_date'] = {}
            if start_date:
                mongo_filters['order_date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                mongo_filters['order_date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')

        # Branch filter
        branch = request.GET.get('branch')
        if branch:
            mongo_filters['po_branch'] = branch

        # Use MongoDB aggregation to group by company
        companies = analytics_mongodb.aggregate_companies(company_code, mongo_filters)

        return JsonResponse({
            'success': True,
            'vendor_name': vendor_name,
            'companies': companies
        })

    except Exception as e:
        logger.error(f"Error querying vendor company breakdown: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def monthly_trends(request):
    """
    Get monthly spending trends.
    GET params: start_date, end_date, vendor_name, branch
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Build MongoDB filters
        mongo_filters = {}

        # Date range filter
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date or end_date:
            mongo_filters['order_date'] = {}
            if start_date:
                mongo_filters['order_date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                mongo_filters['order_date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')

        # Vendor filter
        vendor_name = request.GET.get('vendor_name')
        if vendor_name:
            mongo_filters['po_payto_name'] = {'$regex': vendor_name, '$options': 'i'}

        # Branch filter
        branch = request.GET.get('branch')
        if branch:
            mongo_filters['po_branch'] = branch

        # Use MongoDB aggregation
        trends = analytics_mongodb.aggregate_monthly_trends(company_code, mongo_filters)

        return JsonResponse({'success': True, 'trends': trends})

    except Exception as e:
        logger.error(f"Error querying monthly trends: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def top_vendors(request):
    """
    Get top N vendors by spending with pagination.
    GET params: limit (default 10), offset (default 0), start_date, end_date
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))

        # Build MongoDB filters
        mongo_filters = {}

        # Date range filter
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date or end_date:
            mongo_filters['order_date'] = {}
            if start_date:
                mongo_filters['order_date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                mongo_filters['order_date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')

        # Use MongoDB aggregation and apply pagination
        all_vendors = analytics_mongodb.aggregate_vendors(company_code, mongo_filters)
        total_count = len(all_vendors)
        vendors = all_vendors[offset:offset + limit]

        return JsonResponse({
            'success': True,
            'vendors': vendors,
            'total_count': total_count,
            'offset': offset,
            'limit': limit,
            'has_more': offset + limit < total_count
        })

    except Exception as e:
        logger.error(f"Error querying top vendors: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def export_csv(request):
    """
    Export filtered PO data to CSV.
    GET params: vendor_name, start_date, end_date, company, branch
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Build MongoDB query
        query = {'company_code': company_code}

        # Apply filters
        vendor_name = request.GET.get('vendor_name')
        if vendor_name:
            query['po_payto_name'] = {'$regex': vendor_name, '$options': 'i'}

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date or end_date:
            query['order_date'] = {}
            if start_date:
                query['order_date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                query['order_date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')

        po_company = request.GET.get('company')
        if po_company:
            query['po_company'] = po_company

        branch = request.GET.get('branch')
        if branch:
            query['po_branch'] = branch

        # Get data from MongoDB
        purchase_orders = list(analytics_mongodb.purchase_orders.find(query).sort('order_date', -1))

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="po_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['PO Number', 'Vendor', 'Company', 'Branch', 'Order Total', 'Order Date'])

        for po in purchase_orders:
            writer.writerow([
                po.get('po_number', ''),
                po.get('po_payto_name', ''),
                po.get('po_company', ''),
                po.get('po_branch', ''),
                po.get('order_total', 0),
                po.get('order_date', datetime.now()).strftime('%m/%d/%Y') if po.get('order_date') else '',
            ])

        return response

    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_filter_options(request):
    """
    Get available filter options (vendors, branches, companies).
    Used to populate dropdown filters.
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Use MongoDB service to get filter options
        filter_options = analytics_mongodb.get_filter_options(company_code)

        return JsonResponse({
            'success': True,
            'vendors': sorted(filter_options['vendors']),
            'branches': sorted(filter_options['branches']),
            'companies': sorted(filter_options['companies']),
        })

    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def import_history(request):
    """
    Get import history for the company.
    Shows all past imports with stats.
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Get recent imports from MongoDB (last 50)
        imports = analytics_mongodb.get_import_history(company_code, limit=50)

        # Convert MongoDB documents to JSON-serializable format
        import_list = []
        for imp in imports:
            import_dict = {
                'id': str(imp['_id']),
                'import_batch_id': imp.get('import_batch_id', ''),
                'filename': imp.get('filename', ''),
                'company_code': imp.get('company_code', ''),
                'imported_by_email': imp.get('imported_by_email', ''),
                'status': imp.get('status', ''),
                'total_rows': imp.get('total_rows', 0),
                'imported_rows': imp.get('imported_rows', 0),
                'skipped_rows': imp.get('skipped_rows', 0),
                'error_rows': imp.get('error_rows', 0),
                'imported_at': imp.get('imported_at').isoformat() if imp.get('imported_at') else None,
                'error_message': imp.get('error_message', '')
            }
            import_list.append(import_dict)

        return JsonResponse({
            'success': True,
            'imports': import_list
        })

    except Exception as e:
        logger.error(f"Error getting import history: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["DELETE", "POST"])
def delete_import_batch(request, batch_id):
    """
    Delete an entire import batch.
    Removes all PurchaseOrders associated with the batch_id.
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')
        user_email = request.session.get('customer_email') or request.session.get('admin_username', 'unknown')

        # Verify batch belongs to this company (get from MongoDB)
        import_log = analytics_mongodb.get_import_log(batch_id)

        if not import_log or import_log.get('company_code') != company_code:
            return JsonResponse({'success': False, 'error': 'Import batch not found'}, status=404)

        # Delete all POs in this batch from MongoDB
        deleted_count = analytics_mongodb.delete_by_batch_id(batch_id, company_code)

        # Update import log status in MongoDB
        analytics_mongodb.update_import_log(batch_id, {
            'status': 'deleted',
            'error_message': f"Deleted by {user_email} on {datetime.now().isoformat()}"
        })

        return JsonResponse({
            'success': True,
            'message': f'Deleted {deleted_count} purchase orders from batch {batch_id[:8]}...',
            'deleted_count': deleted_count
        })

    except Exception as e:
        logger.error(f"Error deleting import batch: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["DELETE", "POST"])
def clear_all_data(request):
    """
    NUCLEAR OPTION: Clear all PO data for the company.
    Requires confirmation parameter.
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')
        user_email = request.session.get('customer_email') or request.session.get('admin_username', 'unknown')

        # Require confirmation
        confirmation = request.POST.get('confirm', '') if request.method == 'POST' else request.GET.get('confirm', '')
        if confirmation != 'DELETE_ALL_DATA':
            return JsonResponse({
                'success': False,
                'error': 'Confirmation required. Send confirm=DELETE_ALL_DATA to proceed.'
            }, status=400)

        # Delete all POs for this company from MongoDB
        po_count = analytics_mongodb.delete_all_company_data(company_code)

        # Mark all import logs as deleted in MongoDB
        import_logs = analytics_mongodb.get_import_history(company_code, limit=1000)
        for log in import_logs:
            analytics_mongodb.update_import_log(log['import_batch_id'], {
                'status': 'deleted',
                'error_message': f"All data cleared by {user_email} on {datetime.now().isoformat()}"
            })

        return JsonResponse({
            'success': True,
            'message': f'Cleared all data: {po_count} purchase orders deleted',
            'deleted_count': po_count
        })

    except Exception as e:
        logger.error(f"Error clearing all data: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def batch_stats(request, batch_id):
    """
    Get statistics for a specific import batch.
    """
    try:
        company_code = request.session.get('customer_company_code') or request.session.get('admin_company_code', 'heritage')

        # Get batch info from MongoDB
        import_log = analytics_mongodb.get_import_log(batch_id)

        if not import_log or import_log.get('company_code') != company_code:
            return JsonResponse({'success': False, 'error': 'Batch not found'}, status=404)

        # Get PO count for this batch from MongoDB
        current_po_count = analytics_mongodb.count_purchase_orders(company_code, {'import_batch_id': batch_id})

        # Get total spending for this batch using aggregation
        pipeline = [
            {'$match': {'import_batch_id': batch_id, 'company_code': company_code}},
            {'$group': {'_id': None, 'total': {'$sum': '$order_total'}}}
        ]
        result = list(analytics_mongodb.purchase_orders.aggregate(pipeline))
        total_spent = result[0]['total'] if result else 0

        # Convert import log to JSON-serializable format
        batch_dict = {
            'id': str(import_log['_id']),
            'import_batch_id': import_log.get('import_batch_id', ''),
            'filename': import_log.get('filename', ''),
            'company_code': import_log.get('company_code', ''),
            'imported_by_email': import_log.get('imported_by_email', ''),
            'status': import_log.get('status', ''),
            'total_rows': import_log.get('total_rows', 0),
            'imported_rows': import_log.get('imported_rows', 0),
            'skipped_rows': import_log.get('skipped_rows', 0),
            'error_rows': import_log.get('error_rows', 0),
            'imported_at': import_log.get('imported_at').isoformat() if import_log.get('imported_at') else None,
            'error_message': import_log.get('error_message', '')
        }

        return JsonResponse({
            'success': True,
            'batch': batch_dict,
            'current_po_count': current_po_count,
            'total_spent': float(total_spent)
        })

    except Exception as e:
        logger.error(f"Error getting batch stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
