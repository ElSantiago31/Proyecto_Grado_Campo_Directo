"""
URLs del frontend para Campo Directo
"""

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'frontend'

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),
    path('legal/', views.legal_view, name='legal'),
    
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
    
    # Recuperación de contraseña (vistas integradas de Django)
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html', 
             email_template_name='registration/password_reset_email.html',
             success_url=reverse_lazy('frontend:password_reset_done')
         ), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url=reverse_lazy('frontend:password_reset_complete')
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    # Health check
    path('health/', views.health_check_frontend, name='health-check'),
]
