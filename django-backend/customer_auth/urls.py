from django.urls import path
from . import views

app_name = 'customer_auth'

urlpatterns = [
    path('', views.customer_login_page, name='login_page'),
    path('api/', views.customer_login_api, name='login_api'),
    path('logout/', views.customer_logout, name='logout'),
    path('test-erp/', views.customer_test_erp, name='test_erp'),
    path('update-port/', views.customer_update_port, name='update_port'),
]