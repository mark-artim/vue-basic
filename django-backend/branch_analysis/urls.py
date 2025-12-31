"""
URL Configuration for Branch Transfer Analysis
"""

from django.urls import path
from . import views

app_name = 'branch_analysis'

urlpatterns = [
    path('transfers/', views.branch_transfer_analysis, name='transfer_analysis'),
    path('api/branches/<str:branch_id>/', views.get_branch, name='get_branch'),
    path('api/customers/<str:customer_id>/', views.get_customer, name='get_customer'),
    path('api/geocode/', views.geocode_address, name='geocode_address'),
]
