"""
Analytics URL Configuration
"""

from django.urls import path
from . import views
from . import views_duckdb
from . import views_parquet_import

app_name = 'analytics'

urlpatterns = [
    # Main page
    path('po-insights/', views.po_insights, name='po_insights'),

    # Import
    path('api/import-csv/', views.import_csv, name='import_csv'),
    path('api/import-status/<str:batch_id>/', views.import_status, name='import_status'),
    path('api/import-history/', views.import_history, name='import_history'),

    # Query endpoints
    path('api/query-vendors/', views.query_vendors, name='query_vendors'),
    path('api/query-branches/', views.query_branches, name='query_branches'),
    path('api/query-companies/', views.query_companies, name='query_companies'),
    path('api/vendor/<str:vendor_name>/companies/', views.vendor_company_breakdown, name='vendor_company_breakdown'),
    path('api/monthly-trends/', views.monthly_trends, name='monthly_trends'),

    # Pre-built reports
    path('api/top-vendors/', views.top_vendors, name='top_vendors'),

    # Export
    path('api/export-csv/', views.export_csv, name='export_csv'),

    # Filter options
    path('api/filter-options/', views.get_filter_options, name='filter_options'),

    # Data management
    path('api/batch/<str:batch_id>/delete/', views.delete_import_batch, name='delete_batch'),
    path('api/batch/<str:batch_id>/stats/', views.batch_stats, name='batch_stats'),
    path('api/clear-all-data/', views.clear_all_data, name='clear_all_data'),

    # DuckDB-powered analytics (10-100x faster, queries Parquet from S3)
    path('duckdb/vendors/', views_duckdb.po_vendor_analysis, name='duckdb_vendors'),
    path('duckdb/branches/', views_duckdb.po_branch_analysis, name='duckdb_branches'),
    path('duckdb/trends/', views_duckdb.po_monthly_trends, name='duckdb_trends'),
    path('duckdb/search/', views_duckdb.po_search, name='duckdb_search'),
    path('duckdb/top-by-branch/', views_duckdb.po_top_vendors_by_branch, name='duckdb_top_by_branch'),
    path('duckdb/summary/', views_duckdb.po_summary_stats, name='duckdb_summary'),

    # Parquet-based CSV imports (replaces MongoDB import)
    path('parquet/import/', views_parquet_import.import_csv_to_parquet, name='parquet_import'),
    path('parquet/replace/', views_parquet_import.replace_parquet_file, name='parquet_replace'),
    path('parquet/info/', views_parquet_import.parquet_file_info, name='parquet_info'),
]
