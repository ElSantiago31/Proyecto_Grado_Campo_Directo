"""
Vistas para productos y categorías
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import CategoriaProducto, Producto
from .serializers import (
    CategoriaProductoSerializer, ProductoListSerializer,
    ProductoDetailSerializer, ProductoCreateUpdateSerializer,
    ProductoStockUpdateSerializer
)


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

class IsCampesinoForCreate(permissions.BasePermission):
    """
    Permiso que bloquea la inyección (POST) si el usuario autenticado no es explícitamente un 'campesino'.
    """
    def has_permission(self, request, view):
        if request.method == 'POST':
            return bool(request.user and request.user.is_authenticated and request.user.tipo_usuario == 'campesino')
        return True

class CategoriaProductoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para categorías de productos (solo lectura)
    """
    queryset = CategoriaProducto.objects.filter(estado='activo')
    serializer_class = CategoriaProductoSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']

    @swagger_auto_schema(
        operation_description="Obtener productos de una categoría específica",
        responses={200: ProductoListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def productos(self, request, pk=None):
        """Obtener productos de una categoría"""
        categoria = self.get_object()
        # Solo mostrar productos de campesinos activos y productos disponibles
        productos = categoria.productos.filter(estado='disponible', usuario__estado='activo')
        
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


class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para productos con todas las operaciones CRUD
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCampesinoForCreate, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'estado', 'calidad', 'unidad_medida', 'disponible_entrega_inmediata']
    search_fields = ['nombre', 'descripcion', 'tags', 'usuario__nombre', 'usuario__apellido']
    ordering_fields = ['precio_por_kg', 'fecha_creacion', 'stock_disponible', 'nombre']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        """Optimizar consultas y filtros"""
        # Filtrar por defecto solo productos de usuarios ACTIVOS (Sanciones)
        queryset = Producto.objects.filter(usuario__estado='activo').select_related(
            'usuario', 'finca', 'categoria'
        )
        
        # Filtros personalizados
        if self.action == 'list':
            # Solo mostrar productos disponibles en la lista pública
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(estado='disponible')
            elif hasattr(self.request.user, 'tipo_usuario'):
                # Si es campesino, mostrar sus productos + los disponibles de otros
                if self.request.user.tipo_usuario == 'campesino':
                    queryset = queryset.filter(
                        Q(usuario=self.request.user) | Q(estado='disponible')
                    )
        
        # Filtros adicionales por query params
        precio_min = self.request.query_params.get('precio_min')
        precio_max = self.request.query_params.get('precio_max')
        ubicacion = self.request.query_params.get('ubicacion')
        
        if precio_min:
            queryset = queryset.filter(precio_por_kg__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio_por_kg__lte=precio_max)
        if ubicacion:
            queryset = queryset.filter(
                Q(finca__ubicacion_departamento__icontains=ubicacion) |
                Q(finca__ubicacion_municipio__icontains=ubicacion)
            )
        
        return queryset

    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'list':
            return ProductoListSerializer
        elif self.action == 'retrieve':
            return ProductoDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductoCreateUpdateSerializer
        return ProductoDetailSerializer

    def perform_create(self, serializer):
        """Personalizar creación"""
        # Validar que el usuario sea campesino
        if not self.request.user.tipo_usuario == 'campesino':
            raise permissions.PermissionDenied("Solo los campesinos pueden crear productos")
        
        serializer.save(usuario=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Eliminar producto con soft-delete inteligente"""
        from django.db.models.deletion import ProtectedError
        producto = self.get_object()

        # Verificar propiedad
        if producto.usuario != request.user:
            return Response(
                {'error': 'No tienes permisos para eliminar este producto'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            producto.delete()
            return Response(
                {'message': 'Producto eliminado correctamente'},
                status=status.HTTP_200_OK
            )
        except ProtectedError:
            # El producto tiene pedidos → marcarlo inactivo (soft delete)
            producto.estado = 'inactivo'
            producto.save(update_fields=['estado'])
            return Response(
                {
                    'message': 'El producto tiene pedidos asociados y no puede eliminarse. Fue marcado como inactivo y ya no aparecerá en el catálogo.',
                    'estado': 'inactivo'
                },
                status=status.HTTP_200_OK
            )

    @swagger_auto_schema(
        operation_description="Actualizar stock de un producto",
        request_body=ProductoStockUpdateSerializer,
        responses={
            200: openapi.Response("Stock actualizado correctamente"),
            400: openapi.Response("Error de validación"),
            403: openapi.Response("Sin permisos"),
            404: openapi.Response("Producto no encontrado")
        }
    )
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def actualizar_stock(self, request, pk=None):
        """Actualizar stock de un producto"""
        producto = self.get_object()
        
        # Verificar permisos
        if producto.usuario != request.user:
            return Response(
                {'error': 'No tienes permisos para actualizar este producto'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProductoStockUpdateSerializer(
            data=request.data, 
            context={'producto': producto}
        )
        
        if serializer.is_valid():
            cantidad = serializer.validated_data['cantidad']
            accion = serializer.validated_data['accion']
            
            if accion == 'set':
                producto.stock_disponible = cantidad
            elif accion == 'add':
                producto.aumentar_stock(cantidad)
            elif accion == 'subtract':
                producto.reducir_stock(cantidad)
            
            producto.save()
            
            return Response({
                'message': 'Stock actualizado correctamente',
                'nuevo_stock': producto.stock_disponible,
                'estado': producto.estado
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Obtener productos del campesino autenticado",
        responses={200: ProductoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def mis_productos(self, request):
        """Obtener productos del campesino autenticado"""
        if not request.user.tipo_usuario == 'campesino':
            return Response(
                {'error': 'Solo disponible para campesinos'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        productos = self.get_queryset().filter(usuario=request.user).exclude(estado='inactivo')
        serializer = ProductoListSerializer(productos, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Buscar productos por múltiples criterios",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Búsqueda general", type=openapi.TYPE_STRING),
            openapi.Parameter('categoria', openapi.IN_QUERY, description="ID de categoría", type=openapi.TYPE_INTEGER),
            openapi.Parameter('precio_min', openapi.IN_QUERY, description="Precio mínimo", type=openapi.TYPE_NUMBER),
            openapi.Parameter('precio_max', openapi.IN_QUERY, description="Precio máximo", type=openapi.TYPE_NUMBER),
            openapi.Parameter('ubicacion', openapi.IN_QUERY, description="Filtro por ubicación", type=openapi.TYPE_STRING),
            openapi.Parameter('disponible', openapi.IN_QUERY, description="Solo disponibles", type=openapi.TYPE_BOOLEAN),
        ],
        responses={200: ProductoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Búsqueda avanzada de productos"""
        queryset = self.get_queryset()
        
        # Búsqueda general
        q = request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q) |
                Q(tags__icontains=q) |
                Q(usuario__nombre__icontains=q) |
                Q(usuario__apellido__icontains=q)
            )
        
        # Filtro por disponibilidad
        disponible = request.query_params.get('disponible')
        if disponible and disponible.lower() == 'true':
            queryset = queryset.filter(estado='disponible', stock_disponible__gt=0)
        
        # Aplicar filtros estándar
        queryset = self.filter_queryset(queryset)
        
        # Paginar resultados
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductoListSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Verificar disponibilidad para una cantidad específica",
        manual_parameters=[
            openapi.Parameter('cantidad', openapi.IN_QUERY, description="Cantidad deseada", type=openapi.TYPE_NUMBER, required=True)
        ],
        responses={200: openapi.Response(
            "Información de disponibilidad",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'disponible': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'mensaje': openapi.Schema(type=openapi.TYPE_STRING),
                    'cantidad_maxima': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'precio_total': openapi.Schema(type=openapi.TYPE_NUMBER)
                }
            )
        )}
    )
    @action(detail=True, methods=['get'])
    def verificar_disponibilidad(self, request, pk=None):
        """Verificar disponibilidad de un producto para una cantidad específica"""
        producto = self.get_object()
        
        try:
            cantidad = float(request.query_params.get('cantidad', 0))
        except ValueError:
            return Response(
                {'error': 'Cantidad debe ser un número válido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        disponible, mensaje = producto.puede_ser_comprado_por_cantidad(cantidad)
        
        response_data = {
            'disponible': disponible,
            'mensaje': mensaje,
            'cantidad_maxima': min(producto.stock_disponible, producto.peso_maximo_venta),
            'stock_actual': producto.stock_disponible,
            'precio_unitario': producto.precio_por_kg
        }
        
        if disponible:
            response_data['precio_total'] = producto.calcular_precio_total(cantidad)
        
        return Response(response_data)
