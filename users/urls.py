"""
URLs para autenticación y gestión de usuarios
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Autenticación JWT
    path('register/', views.RegisterView.as_view(), name='auth-register'),
    path('login/', views.LoginView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Perfil de usuario
    path('profile/', views.ProfileView.as_view(), name='auth-profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='auth-profile-update'),
    path('change-password/', views.ChangePasswordView.as_view(), name='auth-change-password'),
    
    # Información de usuario
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    
    # Estadísticas del usuario
    path('dashboard/', views.UserDashboardView.as_view(), name='user-dashboard'),
]