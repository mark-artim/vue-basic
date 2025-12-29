"""
File Management URL Routes

All routes require authentication and enforce company isolation.
"""

from django.urls import path
from . import views

app_name = 'files'

urlpatterns = [
    # File Manager Page (HTML)
    path('', views.file_manager_page, name='manager'),

    # File CRUD operations (API endpoints)
    path('list/', views.list_files, name='list'),
    path('upload/', views.upload_file, name='upload'),
    path('download/<str:file_id>/', views.download_file, name='download'),
    path('delete/<str:file_id>/', views.delete_file, name='delete'),
    path('rename/<str:file_id>/', views.rename_file, name='rename'),
]
