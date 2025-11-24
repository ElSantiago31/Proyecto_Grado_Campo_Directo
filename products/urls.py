"""
URLs para productos y categorías
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'categorias', views.CategoriaProductoViewSet)
router.register(r'productos', views.ProductoViewSet, basename='producto')

urlpatterns = [
    path('', include(router.urls)),
]