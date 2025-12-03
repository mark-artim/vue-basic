from django.urls import path
from . import views

app_name = 'pdw'

urlpatterns = [
    path('', views.pdw_upload, name='upload'),
    path('parse/', views.pdw_parse, name='parse'),
    path('preview/', views.pdw_preview, name='preview'),
    path('apply-rule/', views.pdw_apply_rule, name='apply_rule'),
    path('smart-clean/', views.pdw_smart_clean, name='smart_clean'),
    path('paginate/', views.pdw_paginate, name='paginate'),
    path('export/', views.pdw_export, name='export'),
]
