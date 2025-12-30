"""
URL Configuration for Invoice Lookup
"""

from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    # Main invoice lookup page
    path('lookup/', views.invoice_lookup, name='invoice_lookup'),

    # API endpoints
    path('api/customers/search/', views.search_customers, name='search_customers'),
    path('api/customers/<str:customer_id>/', views.get_customer, name='get_customer'),
    path('api/invoices/search/', views.search_invoices, name='search_invoices'),
    path('api/invoices/pdf/<str:full_invoice_id>/', views.get_invoice_pdf, name='get_invoice_pdf'),
]
