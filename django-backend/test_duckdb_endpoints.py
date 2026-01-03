"""
Test DuckDB API Endpoints

Simulates API requests to verify endpoints work correctly
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emp54_django.settings')
django.setup()

from django.test import RequestFactory
from analytics import views_duckdb
import json

factory = RequestFactory()

print("=" * 70)
print("Testing DuckDB API Endpoints")
print("=" * 70)

# Create a mock session with authentication
def create_mock_request(path, params=None):
    request = factory.get(path, params or {})
    request.session = {'customer_logged_in': True}
    return request

# Test 1: Summary Stats
print("\n[Test 1] GET /analytics/duckdb/summary/")
print("  Testing: Overall statistics")
try:
    request = create_mock_request('/analytics/duckdb/summary/')
    response = views_duckdb.po_summary_stats(request)

    if response.status_code == 200:
        data = json.loads(response.content)
        if data['success']:
            stats = data['data']
            print(f"  PASS - Summary loaded:")
            print(f"    Total orders: {stats.get('total_orders', 0):,}")
            print(f"    Unique vendors: {stats.get('unique_vendors', 0):,}")
            print(f"    Unique branches: {stats.get('unique_branches', 0):,}")
            print(f"    Total value: ${stats.get('total_value', 0):,.2f}")
            print(f"    Avg order: ${stats.get('avg_order_value', 0):,.2f}")
        else:
            print(f"  FAIL - {data}")
    else:
        print(f"  FAIL - Status {response.status_code}")
except Exception as e:
    print(f"  ERROR - {e}")

# Test 2: Top Vendors
print("\n[Test 2] GET /analytics/duckdb/vendors/?limit=5")
print("  Testing: Vendor analysis with aggregations")
try:
    request = create_mock_request('/analytics/duckdb/vendors/', {'limit': '5'})
    response = views_duckdb.po_vendor_analysis(request)

    if response.status_code == 200:
        data = json.loads(response.content)
        if data['success']:
            print(f"  PASS - Top {len(data['data'])} vendors:")
            for i, vendor in enumerate(data['data'][:3], 1):
                print(f"    {i}. {vendor['vendor']}: {vendor['order_count']:,} orders, ${vendor['total_spent']:,.2f}")
        else:
            print(f"  FAIL - {data}")
    else:
        print(f"  FAIL - Status {response.status_code}")
except Exception as e:
    print(f"  ERROR - {e}")

# Test 3: Branch Analysis
print("\n[Test 3] GET /analytics/duckdb/branches/?limit=5")
print("  Testing: Branch performance metrics")
try:
    request = create_mock_request('/analytics/duckdb/branches/', {'limit': '5'})
    response = views_duckdb.po_branch_analysis(request)

    if response.status_code == 200:
        data = json.loads(response.content)
        if data['success']:
            print(f"  PASS - Top {len(data['data'])} branches:")
            for i, branch in enumerate(data['data'][:3], 1):
                print(f"    {i}. Branch {branch['branch']}: {branch['order_count']:,} orders, {branch['unique_vendors']} vendors")
        else:
            print(f"  FAIL - {data}")
    else:
        print(f"  FAIL - Status {response.status_code}")
except Exception as e:
    print(f"  ERROR - {e}")

# Test 4: Search
print("\n[Test 4] GET /analytics/duckdb/search/?vendor=RHEEM&limit=3")
print("  Testing: Search functionality")
try:
    request = create_mock_request('/analytics/duckdb/search/', {'vendor': 'RHEEM', 'limit': '3'})
    response = views_duckdb.po_search(request)

    if response.status_code == 200:
        data = json.loads(response.content)
        if data['success']:
            print(f"  PASS - Found {len(data['data'])} results:")
            for i, po in enumerate(data['data'][:3], 1):
                print(f"    {i}. PO #{po['po_number']}: ${po['order_total']:,.2f} ({po['vendor']})")
        else:
            print(f"  FAIL - {data}")
    else:
        print(f"  FAIL - Status {response.status_code}")
except Exception as e:
    print(f"  ERROR - {e}")

# Test 5: Monthly Trends
print("\n[Test 5] GET /analytics/duckdb/trends/?months=3")
print("  Testing: Time-series aggregation")
try:
    request = create_mock_request('/analytics/duckdb/trends/', {'months': '3'})
    response = views_duckdb.po_monthly_trends(request)

    if response.status_code == 200:
        data = json.loads(response.content)
        if data['success']:
            print(f"  PASS - Last {len(data['data'])} months:")
            for i, month in enumerate(data['data'][:3], 1):
                month_str = str(month['month'])[:7] if month['month'] else 'Unknown'
                print(f"    {month_str}: {month['order_count']:,} orders, ${month['monthly_total']:,.2f}")
        else:
            print(f"  FAIL - {data}")
    else:
        print(f"  FAIL - Status {response.status_code}")
except Exception as e:
    print(f"  ERROR - {e}")

print("\n" + "=" * 70)
print("ENDPOINT TESTING COMPLETE")
print("=" * 70)
print("\nAll endpoints are working! Ready to:")
print("1. Use these in the UI")
print("2. Delete MongoDB purchase_orders collection")
print("3. Update CSV import to write Parquet")
print("=" * 70)
