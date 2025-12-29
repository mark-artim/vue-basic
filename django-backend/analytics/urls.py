"""
Analytics URL Configuration
"""

from django.urls import path
from . import views

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
]
