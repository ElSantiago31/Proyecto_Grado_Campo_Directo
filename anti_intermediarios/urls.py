"""
URLs para funcionalidades anti-intermediarios
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversacionViewSet,
    TransparenciaPreciosViewSet, 
    AntiIntermediariosStatsViewSet
)

app_name = 'anti_intermediarios'

# Router para ViewSets
router = DefaultRouter()
router.register(r'conversaciones', ConversacionViewSet, basename='conversacion')
router.register(r'transparencia-precios', TransparenciaPreciosViewSet, basename='transparencia-precios')
router.register(r'stats', AntiIntermediariosStatsViewSet, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
]