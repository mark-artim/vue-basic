"""
URL Configuration for Branch Transfer Analysis
"""

from django.urls import path
from . import views

app_name = 'branch_analysis'

urlpatterns = [
    path('transfers/', views.branch_transfer_analysis, name='transfer_analysis'),
]
