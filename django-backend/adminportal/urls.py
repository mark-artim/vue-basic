from django.urls import path
from . import views

app_name = 'adminportal'

urlpatterns = [
    path('login/', views.admin_login_page, name='login_page'),
    path('login/api/', views.admin_login_api, name='login_api'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('logs/', views.admin_logs_page, name='logs_page'),
    path('api/logs/', views.admin_logs_api, name='logs_api'),
    path('logout/', views.admin_logout, name='logout'),
    path('test-erp/', views.admin_test_erp, name='test_erp'),
]