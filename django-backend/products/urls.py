from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('merge/', views.product_merge_page, name='merge_page'),
    path('compare/', views.product_compare_page, name='compare_page'),
    path('search/', views.product_search_api, name='search_api'),
    path('api/get/<str:product_id>/', views.product_get_api, name='get_api'),
    path('merge/save/', views.product_merge_save, name='merge_save'),
    path('test-erp/', views.test_erp_connection, name='test_erp'),
]