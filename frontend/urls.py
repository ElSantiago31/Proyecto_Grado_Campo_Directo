"""
URLs del frontend para Campo Directo
"""

from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),
    
    # Autenticación
    path('login/', views.login_page, name='login'),
    path('login-comprador/', views.login_comprador, name='login-comprador'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.register_page, name='register'),
    path('registro-exitoso/', views.registro_exitoso, name='registro-exitoso'),
    
    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-comprador/', views.dashboard_comprador, name='dashboard-comprador'),
    path('dashboard-redirect/', views.dashboard_redirect, name='dashboard-redirect'),
    
    # Health check
    path('health/', views.health_check_frontend, name='health-check'),
]
