"""
URL Configuration for Vendor Management
"""

from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    # Main vendor add page
    path('add/', views.vendor_add, name='vendor_add'),

    # API endpoints
    path('api/search-payto/', views.search_payto_vendors, name='search_payto'),
    path('api/shipfrom/<str:payto_id>/', views.get_shipfrom_vendors, name='get_shipfrom'),
    path('api/create/', views.create_vendors, name='create_vendors'),
]
