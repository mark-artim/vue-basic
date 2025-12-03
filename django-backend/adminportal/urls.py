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

    # User Management
    path('users/', views.admin_users_page, name='users_page'),
    path('api/users/', views.admin_users_list_api, name='users_list_api'),
    path('api/users/save/', views.admin_users_save_api, name='users_save_api'),
    path('api/users/<str:user_id>/delete/', views.admin_users_delete_api, name='users_delete_api'),
    path('api/companies/', views.admin_companies_list_api, name='companies_list_api'),
    path('api/products/', views.admin_products_list_api, name='products_list_api'),
    path('api/users/invite/', views.admin_send_invite_api, name='users_invite_api'),
]