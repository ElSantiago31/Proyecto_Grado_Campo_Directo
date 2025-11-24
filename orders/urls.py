"""
URLs para pedidos
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'pedidos', views.PedidoViewSet, basename='pedido')

urlpatterns = [
    path('', include(router.urls)),
]