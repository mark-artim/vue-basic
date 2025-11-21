"""
URL configuration for emp54_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import redirect
from core import views as core_views

def home_view(request):
    """Redirect root to login page"""
    return redirect('/login/')

def customer_dashboard_redirect(request):
    """Redirect /dashboard/ to customer dashboard - new Tailwind version"""
    from customer_auth.views import customer_home_tailwind
    return customer_home_tailwind(request)

urlpatterns = [
    path('', home_view, name='home'),
    path('django-admin/', admin.site.urls),  # Django's built-in admin
    path('admin/', include('adminportal.urls')),  # EMP54 Admin Portal
    path('login/', include('customer_auth.urls')),  # Customer Login
    path('dashboard/', customer_dashboard_redirect, name='customer_dashboard'),  # Customer Dashboard redirect
    path('products/', include('products.urls')),
    path('pdw/', include('pdw.urls')),  # PDW Data Prep
    path('api/switch-port/', core_views.switch_port, name='switch_port'),  # Port selector API
]
