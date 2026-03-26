"""
URLs para fincas y certificaciones
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'fincas', views.FincaViewSet, basename='finca')

urlpatterns = [
    path('', include(router.urls)),
]