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

from .models import Finca, Certificacion
from .serializers import (
    FincaListSerializer, FincaDetailSerializer, FincaCreateUpdateSerializer,
    CertificacionSerializer, CertificacionCreateUpdateSerializer
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
        queryset = Finca.objects.select_related('usuario').prefetch_related('certificaciones')
        
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

    @swagger_auto_schema(
        operation_description="Obtener certificaciones de una finca",
        responses={200: CertificacionSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def certificaciones(self, request, pk=None):
        """Obtener certificaciones de una finca"""
        finca = self.get_object()
        certificaciones = finca.certificaciones.all()
        
        # Filtrar por estado si se especifica
        estado = request.query_params.get('estado')
        if estado:
            certificaciones = certificaciones.filter(estado=estado)
        
        serializer = CertificacionSerializer(certificaciones, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Buscar fincas por ubicación",
        manual_parameters=[
            openapi.Parameter('ubicacion', openapi.IN_QUERY, description="Término de búsqueda para ubicación", type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: FincaListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def buscar_por_ubicacion(self, request):
        """Buscar fincas por ubicación"""
        ubicacion = request.query_params.get('ubicacion')
        if not ubicacion:
            return Response(
                {'error': 'Debe proporcionar el parámetro ubicacion'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            Q(ubicacion_departamento__icontains=ubicacion) |
            Q(ubicacion_municipio__icontains=ubicacion) |
            Q(direccion__icontains=ubicacion)
        )
        
        # Aplicar filtros estándar
        queryset = self.filter_queryset(queryset)
        
        serializer = FincaListSerializer(queryset, many=True)
        return Response(serializer.data)


class CertificacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para certificaciones
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'entidad_certificadora']
    search_fields = ['nombre', 'descripcion', 'entidad_certificadora']
    ordering_fields = ['fecha_obtencion', 'fecha_vencimiento', 'fecha_creacion']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        """Optimizar consultas"""
        queryset = Certificacion.objects.select_related('finca__usuario')
        
        # Si el usuario está autenticado y es campesino, mostrar solo sus certificaciones
        if self.request.user.is_authenticated and hasattr(self.request.user, 'tipo_usuario'):
            if self.request.user.tipo_usuario == 'campesino':
                queryset = queryset.filter(finca__usuario=self.request.user)
        
        return queryset

    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action in ['create', 'update', 'partial_update']:
            return CertificacionCreateUpdateSerializer
        return CertificacionSerializer

    def has_object_permission(self, request, view, obj):
        """Verificar permisos a nivel de objeto"""
        # Permisos de lectura para cualquier request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Permisos de escritura solo para el propietario de la finca
        return obj.finca.usuario == request.user

    def perform_create(self, serializer):
        """Personalizar creación"""
        # Validar que el usuario sea campesino
        if not self.request.user.tipo_usuario == 'campesino':
            raise permissions.PermissionDenied("Solo los campesinos pueden crear certificaciones")
        
        serializer.save()

    @swagger_auto_schema(
        operation_description="Obtener certificaciones vigentes",
        responses={200: CertificacionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def vigentes(self, request):
        """Obtener solo certificaciones vigentes"""
        queryset = self.get_queryset().filter(estado='vigente')
        serializer = CertificacionSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Obtener certificaciones próximas a vencer",
        manual_parameters=[
            openapi.Parameter('dias', openapi.IN_QUERY, description="Número de días de anticipación", type=openapi.TYPE_INTEGER)
        ],
        responses={200: CertificacionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def proximas_a_vencer(self, request):
        """Obtener certificaciones próximas a vencer"""
        from django.utils import timezone
        from datetime import timedelta
        
        dias = int(request.query_params.get('dias', 30))
        fecha_limite = timezone.now().date() + timedelta(days=dias)
        
        queryset = self.get_queryset().filter(
            estado='vigente',
            fecha_vencimiento__lte=fecha_limite,
            fecha_vencimiento__gte=timezone.now().date()
        )
        
        serializer = CertificacionSerializer(queryset, many=True)
        return Response(serializer.data)
