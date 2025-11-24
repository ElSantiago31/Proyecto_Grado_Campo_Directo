"""
Vistas para pedidos y detalles de pedidos
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Pedido, DetallePedido
from .serializers import (
    PedidoListSerializer, PedidoDetailSerializer, PedidoCreateSerializer,
    PedidoUpdateEstadoSerializer, CalificacionSerializer
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para pedidos: solo comprador o campesino pueden ver/editar
    """
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura para comprador y campesino del pedido
        if request.method in permissions.SAFE_METHODS:
            return obj.comprador == request.user or obj.campesino == request.user
        # Permisos de escritura solo para el campesino (cambiar estado)
        return obj.campesino == request.user


class PedidoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para pedidos con operaciones CRUD y acciones especiales
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'metodo_pago', 'campesino', 'comprador']
    search_fields = ['id', 'codigo_seguimiento', 'notas_comprador', 'notas_campesino']
    ordering_fields = ['fecha_pedido', 'total', 'fecha_entrega_programada']
    ordering = ['-fecha_pedido']

    def get_queryset(self):
        """Filtrar pedidos según el tipo de usuario"""
        user = self.request.user
        queryset = Pedido.objects.select_related('comprador', 'campesino').prefetch_related('detalles__producto')
        
        # Filtrar según el tipo de usuario
        if hasattr(user, 'tipo_usuario'):
            if user.tipo_usuario == 'comprador':
                queryset = queryset.filter(comprador=user)
            elif user.tipo_usuario == 'campesino':
                queryset = queryset.filter(campesino=user)
        
        return queryset

    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'list':
            return PedidoListSerializer
        elif self.action == 'retrieve':
            return PedidoDetailSerializer
        elif self.action == 'create':
            return PedidoCreateSerializer
        return PedidoDetailSerializer

    def perform_create(self, serializer):
        """Personalizar creación de pedidos"""
        # Validar que el usuario sea comprador
        if not self.request.user.tipo_usuario == 'comprador':
            raise permissions.PermissionDenied("Solo los compradores pueden crear pedidos")
        
        serializer.save()

    @swagger_auto_schema(
        operation_description="Actualizar estado de un pedido",
        request_body=PedidoUpdateEstadoSerializer,
        responses={
            200: openapi.Response("Estado actualizado correctamente"),
            400: openapi.Response("Error de validación"),
            403: openapi.Response("Sin permisos"),
            404: openapi.Response("Pedido no encontrado")
        }
    )
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def actualizar_estado(self, request, pk=None):
        """Actualizar estado de un pedido (solo campesinos)"""
        pedido = self.get_object()
        
        # Verificar que es el campesino del pedido
        if pedido.campesino != request.user:
            return Response(
                {'error': 'Solo el campesino puede actualizar el estado del pedido'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PedidoUpdateEstadoSerializer(
            data=request.data, 
            context={'pedido': pedido}
        )
        
        if serializer.is_valid():
            nuevo_estado = serializer.validated_data['nuevo_estado']
            notas = serializer.validated_data.get('notas', '')
            
            # Actualizar estado y timestamps
            pedido.actualizar_estado(nuevo_estado)
            
            # Añadir notas si se proporcionaron
            if notas:
                pedido.notas_campesino = notas
                pedido.save()
            
            return Response({
                'message': 'Estado actualizado correctamente',
                'nuevo_estado': nuevo_estado,
                'estado_display': pedido.get_estado_display()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Cancelar un pedido",
        responses={
            200: openapi.Response("Pedido cancelado correctamente"),
            400: openapi.Response("El pedido no puede ser cancelado"),
            403: openapi.Response("Sin permisos")
        }
    )
    @action(detail=True, methods=['patch'])
    def cancelar(self, request, pk=None):
        """Cancelar un pedido"""
        pedido = self.get_object()
        
        # Verificar permisos (comprador o campesino pueden cancelar)
        if request.user != pedido.comprador and request.user != pedido.campesino:
            return Response(
                {'error': 'Sin permisos para cancelar este pedido'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not pedido.puede_ser_cancelado():
            return Response(
                {'error': 'El pedido no puede ser cancelado en su estado actual'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cancelar y restaurar stock
        pedido.actualizar_estado('cancelled')
        
        # Restaurar stock de productos
        for detalle in pedido.detalles.all():
            detalle.producto.aumentar_stock(int(detalle.cantidad))
        
        return Response({'message': 'Pedido cancelado correctamente'})

    @swagger_auto_schema(
        operation_description="Calificar un pedido completado",
        request_body=CalificacionSerializer,
        responses={
            200: openapi.Response("Calificación registrada correctamente"),
            400: openapi.Response("Error de validación"),
            403: openapi.Response("Sin permisos")
        }
    )
    @action(detail=True, methods=['post'])
    def calificar(self, request, pk=None):
        """Calificar un pedido completado"""
        pedido = self.get_object()
        
        serializer = CalificacionSerializer(
            data=request.data, 
            context={'pedido': pedido, 'user': request.user}
        )
        
        if serializer.is_valid():
            calificacion = serializer.validated_data['calificacion']
            comentario = serializer.validated_data.get('comentario', '')
            
            # Aplicar calificación según el tipo de usuario
            if request.user == pedido.comprador:
                pedido.calificacion_comprador = calificacion
                # Actualizar calificación del campesino
                pedido.campesino.actualizar_calificacion(calificacion)
            elif request.user == pedido.campesino:
                pedido.calificacion_campesino = calificacion
                # Actualizar calificación del comprador
                pedido.comprador.actualizar_calificacion(calificacion)
            
            pedido.comentario_calificacion = comentario
            pedido.save()
            
            return Response({'message': 'Calificación registrada correctamente'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Obtener pedidos como comprador",
        responses={200: PedidoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def mis_compras(self, request):
        """Obtener pedidos del usuario como comprador"""
        if not request.user.tipo_usuario == 'comprador':
            return Response(
                {'error': 'Solo disponible para compradores'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        pedidos = self.get_queryset().filter(comprador=request.user)
        serializer = PedidoListSerializer(pedidos, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Obtener pedidos como campesino",
        responses={200: PedidoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def mis_ventas(self, request):
        """Obtener pedidos del usuario como campesino"""
        if not request.user.tipo_usuario == 'campesino':
            return Response(
                {'error': 'Solo disponible para campesinos'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        pedidos = self.get_queryset().filter(campesino=request.user)
        serializer = PedidoListSerializer(pedidos, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Buscar pedido por código de seguimiento",
        manual_parameters=[
            openapi.Parameter('codigo', openapi.IN_QUERY, description="Código de seguimiento", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: PedidoDetailSerializer(),
            404: openapi.Response("Pedido no encontrado")
        }
    )
    @action(detail=False, methods=['get'])
    def buscar_por_codigo(self, request):
        """Buscar pedido por código de seguimiento"""
        codigo = request.query_params.get('codigo')
        if not codigo:
            return Response(
                {'error': 'Debe proporcionar el código de seguimiento'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pedido = self.get_queryset().get(codigo_seguimiento=codigo)
            serializer = PedidoDetailSerializer(pedido)
            return Response(serializer.data)
        except Pedido.DoesNotExist:
            return Response(
                {'error': 'Pedido no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Obtener estadísticas de pedidos",
        responses={
            200: openapi.Response(
                "Estadísticas de pedidos",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_pedidos': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'por_estado': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'ventas_totales': openapi.Schema(type=openapi.TYPE_NUMBER),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de pedidos del usuario"""
        queryset = self.get_queryset()
        
        # Contar pedidos por estado
        estados = {}
        for estado, _ in Pedido.ESTADO_CHOICES:
            estados[estado] = queryset.filter(estado=estado).count()
        
        # Calcular totales
        total_pedidos = queryset.count()
        
        # Ventas totales (para campesinos) o gastos (para compradores)
        pedidos_completados = queryset.filter(estado='completed')
        ventas_totales = sum(pedido.total for pedido in pedidos_completados)
        
        return Response({
            'total_pedidos': total_pedidos,
            'por_estado': estados,
            'ventas_totales': ventas_totales,
            'pedidos_completados': pedidos_completados.count()
        })
