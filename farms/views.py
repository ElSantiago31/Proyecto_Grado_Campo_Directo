"""
Vistas para fincas y certificaciones
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Finca
from .serializers import (
    FincaListSerializer, FincaDetailSerializer, FincaCreateUpdateSerializer
)
from products.serializers import ProductoListSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los propietarios editar
    """
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura para cualquier request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Permisos de escritura solo para el propietario
        return obj.usuario == request.user


class FincaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para fincas con todas las operaciones CRUD
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'tipo_cultivo', 'ubicacion_departamento']
    search_fields = ['nombre_finca', 'descripcion', 'ubicacion_municipio', 'usuario__nombre', 'usuario__apellido']
    ordering_fields = ['area_hectareas', 'fecha_creacion', 'nombre_finca']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        """Optimizar consultas y filtros"""
        queryset = Finca.objects.select_related('usuario')
        
        # Filtros personalizados
        if self.action == 'list':
            # Solo mostrar fincas activas en la lista pública
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(estado='activa')
            elif hasattr(self.request.user, 'tipo_usuario'):
                # Si es campesino, mostrar sus fincas + las activas de otros
                if self.request.user.tipo_usuario == 'campesino':
                    queryset = queryset.filter(
                        Q(usuario=self.request.user) | Q(estado='activa')
                    )
        
        return queryset

    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'list':
            return FincaListSerializer
        elif self.action == 'retrieve':
            return FincaDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FincaCreateUpdateSerializer
        return FincaDetailSerializer

    def perform_create(self, serializer):
        """Personalizar creación"""
        # Validar que el usuario sea campesino
        if not self.request.user.tipo_usuario == 'campesino':
            raise permissions.PermissionDenied("Solo los campesinos pueden crear fincas")
        
        serializer.save(usuario=self.request.user)

    @swagger_auto_schema(
        operation_description="Obtener fincas del campesino autenticado",
        responses={200: FincaListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def mis_fincas(self, request):
        """Obtener fincas del campesino autenticado"""
        if not request.user.tipo_usuario == 'campesino':
            return Response(
                {'error': 'Solo disponible para campesinos'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        fincas = self.get_queryset().filter(usuario=request.user)
        serializer = FincaListSerializer(fincas, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Obtener productos de una finca específica",
        responses={200: ProductoListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def productos(self, request, pk=None):
        """Obtener productos de una finca"""
        finca = self.get_object()
        productos = finca.productos.filter(estado='disponible')
        
        # Aplicar filtros adicionales
        search = request.query_params.get('search')
        if search:
            productos = productos.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(tags__icontains=search)
            )
        
        serializer = ProductoListSerializer(productos, many=True)
        return Response(serializer.data)


