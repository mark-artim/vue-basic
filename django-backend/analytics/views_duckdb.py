"""
Purchase Order Analytics Views using DuckDB

High-performance analytical queries on Parquet files.
Queries 111K+ records in milliseconds directly from Wasabi S3.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from services.duckdb_client import duckdb_client

logger = logging.getLogger(__name__)

# S3 path to purchase orders Parquet file
PO_PARQUET_PATH = 's3://emp54/analytics/purchase_orders.parquet'


@require_http_methods(["GET"])
def po_vendor_analysis(request):
    """
    Analyze purchase orders by vendor

    Query params:
        - limit: Number of vendors to return (default: 20)
        - min_orders: Minimum order count filter (default: 1)
        - sort_by: Sort field (total_spent|order_count, default: total_spent)
    """
    if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        limit = int(request.GET.get('limit', 20))
        min_orders = int(request.GET.get('min_orders', 1))
        sort_by = request.GET.get('sort_by', 'total_spent')

        if sort_by not in ['total_spent', 'order_count']:
            sort_by = 'total_spent'

        sql = f"""
            SELECT
                po_payto_name as vendor,
                po_payto_id as vendor_id,
                COUNT(*) as order_count,
                SUM(order_total) as total_spent,
                AVG(order_total) as avg_order_value,
                MIN(order_total) as min_order,
                MAX(order_total) as max_order,
                MIN(order_date) as first_order_date,
                MAX(order_date) as last_order_date
            FROM '{PO_PARQUET_PATH}'
            WHERE po_payto_name IS NOT NULL
            GROUP BY po_payto_name, po_payto_id
            HAVING COUNT(*) >= {min_orders}
            ORDER BY {sort_by} DESC
            LIMIT {limit}
        """

        results = duckdb_client.query(sql)

        return JsonResponse({
            'success': True,
            'data': results,
            'count': len(results),
            'filters': {
                'limit': limit,
                'min_orders': min_orders,
                'sort_by': sort_by
            }
        })

    except Exception as e:
        logger.error(f"Vendor analysis error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def po_branch_analysis(request):
    """
    Analyze purchase orders by branch

    Query params:
        - limit: Number of branches to return (default: 20)
    """
    if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        limit = int(request.GET.get('limit', 20))

        sql = f"""
            SELECT
                po_branch as branch,
                COUNT(*) as order_count,
                SUM(order_total) as total_value,
                AVG(order_total) as avg_order_value,
                COUNT(DISTINCT po_payto_id) as unique_vendors,
                MIN(order_date) as earliest_order,
                MAX(order_date) as latest_order
            FROM '{PO_PARQUET_PATH}'
            WHERE po_branch IS NOT NULL
            GROUP BY po_branch
            ORDER BY order_count DESC
            LIMIT {limit}
        """

        results = duckdb_client.query(sql)

        return JsonResponse({
            'success': True,
            'data': results,
            'count': len(results)
        })

    except Exception as e:
        logger.error(f"Branch analysis error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def po_monthly_trends(request):
    """
    Monthly spending trends

    Query params:
        - months: Number of months to return (default: 12)
        - branch: Filter by branch (optional)
        - vendor: Filter by vendor name (partial match, optional)
    """
    if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        months = int(request.GET.get('months', 12))
        branch = request.GET.get('branch', '')
        vendor = request.GET.get('vendor', '')

        # Build WHERE clause
        where_clauses = ["order_date IS NOT NULL"]

        if branch:
            where_clauses.append(f"po_branch = '{branch}'")
        if vendor:
            where_clauses.append(f"po_payto_name LIKE '%{vendor}%'")

        where_clause = ' AND '.join(where_clauses)

        sql = f"""
            SELECT
                DATE_TRUNC('month', CAST(order_date AS DATE)) as month,
                COUNT(*) as order_count,
                SUM(order_total) as monthly_total,
                AVG(order_total) as avg_order_value,
                COUNT(DISTINCT po_payto_id) as unique_vendors
            FROM '{PO_PARQUET_PATH}'
            WHERE {where_clause}
                AND order_date >= CURRENT_DATE - INTERVAL '{months} months'
            GROUP BY DATE_TRUNC('month', CAST(order_date AS DATE))
            ORDER BY month DESC
            LIMIT {months}
        """

        results = duckdb_client.query(sql)

        return JsonResponse({
            'success': True,
            'data': results,
            'count': len(results),
            'filters': {
                'months': months,
                'branch': branch or 'all',
                'vendor': vendor or 'all'
            }
        })

    except Exception as e:
        logger.error(f"Monthly trends error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def po_search(request):
    """
    Search purchase orders with filters

    Query params:
        - po_number: PO number (partial match)
        - vendor: Vendor name (partial match)
        - branch: Branch code
        - min_amount: Minimum order total
        - max_amount: Maximum order total
        - start_date: Start date filter (YYYY-MM-DD)
        - end_date: End date filter (YYYY-MM-DD)
        - limit: Result limit (default: 100)
    """
    if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        po_number = request.GET.get('po_number', '')
        vendor = request.GET.get('vendor', '')
        branch = request.GET.get('branch', '')
        min_amount = request.GET.get('min_amount', '')
        max_amount = request.GET.get('max_amount', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        limit = int(request.GET.get('limit', 100))

        # Build WHERE clause
        where_clauses = []

        if po_number:
            where_clauses.append(f"po_number LIKE '%{po_number}%'")
        if vendor:
            where_clauses.append(f"po_payto_name LIKE '%{vendor}%'")
        if branch:
            where_clauses.append(f"po_branch = '{branch}'")
        if min_amount:
            where_clauses.append(f"order_total >= {float(min_amount)}")
        if max_amount:
            where_clauses.append(f"order_total <= {float(max_amount)}")
        if start_date:
            where_clauses.append(f"order_date >= '{start_date}'")
        if end_date:
            where_clauses.append(f"order_date <= '{end_date}'")

        where_clause = ' AND '.join(where_clauses) if where_clauses else '1=1'

        sql = f"""
            SELECT
                po_number,
                po_payto_name as vendor,
                po_payto_id as vendor_id,
                po_branch as branch,
                po_company as company,
                order_total,
                order_date,
                company_code
            FROM '{PO_PARQUET_PATH}'
            WHERE {where_clause}
            ORDER BY order_date DESC
            LIMIT {limit}
        """

        results = duckdb_client.query(sql)

        return JsonResponse({
            'success': True,
            'data': results,
            'count': len(results),
            'filters': {
                'po_number': po_number,
                'vendor': vendor,
                'branch': branch,
                'min_amount': min_amount,
                'max_amount': max_amount,
                'start_date': start_date,
                'end_date': end_date
            }
        })

    except Exception as e:
        logger.error(f"PO search error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def po_top_vendors_by_branch(request):
    """
    Get top vendors for each branch

    Query params:
        - top_n: Number of top vendors per branch (default: 5)
        - min_total: Minimum total spend threshold (default: 0)
    """
    if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        top_n = int(request.GET.get('top_n', 5))
        min_total = float(request.GET.get('min_total', 0))

        sql = f"""
            WITH vendor_stats AS (
                SELECT
                    po_branch as branch,
                    po_payto_name as vendor,
                    COUNT(*) as order_count,
                    SUM(order_total) as total_spent,
                    AVG(order_total) as avg_order_value,
                    RANK() OVER (PARTITION BY po_branch ORDER BY SUM(order_total) DESC) as rank
                FROM '{PO_PARQUET_PATH}'
                WHERE po_branch IS NOT NULL
                    AND po_payto_name IS NOT NULL
                GROUP BY po_branch, po_payto_name
                HAVING SUM(order_total) >= {min_total}
            )
            SELECT
                branch,
                vendor,
                order_count,
                total_spent,
                avg_order_value,
                rank
            FROM vendor_stats
            WHERE rank <= {top_n}
            ORDER BY branch, rank
        """

        results = duckdb_client.query(sql)

        # Group by branch for easier frontend consumption
        grouped = {}
        for row in results:
            branch = row['branch']
            if branch not in grouped:
                grouped[branch] = []
            grouped[branch].append(row)

        return JsonResponse({
            'success': True,
            'data': grouped,
            'branch_count': len(grouped),
            'filters': {
                'top_n': top_n,
                'min_total': min_total
            }
        })

    except Exception as e:
        logger.error(f"Top vendors by branch error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def po_summary_stats(request):
    """
    Get overall summary statistics

    No parameters required
    """
    if not request.session.get('customer_logged_in') and not request.session.get('admin_logged_in'):
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        sql = f"""
            SELECT
                COUNT(*) as total_orders,
                COUNT(DISTINCT po_payto_id) as unique_vendors,
                COUNT(DISTINCT po_branch) as unique_branches,
                SUM(order_total) as total_value,
                AVG(order_total) as avg_order_value,
                MIN(order_total) as min_order,
                MAX(order_total) as max_order,
                MIN(order_date) as earliest_order,
                MAX(order_date) as latest_order
            FROM '{PO_PARQUET_PATH}'
        """

        results = duckdb_client.query(sql)

        return JsonResponse({
            'success': True,
            'data': results[0] if results else {},
        })

    except Exception as e:
        logger.error(f"Summary stats error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
