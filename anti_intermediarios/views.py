"""
Vistas para funcionalidades anti-intermediarios
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.db.models import Q, Avg, Count, Sum, F
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decimal import Decimal
import datetime

from .models import Conversacion, Mensaje, TransparenciaPrecios, ReporteImpacto
from .serializers import (
    ConversacionListSerializer, ConversacionDetailSerializer, ConversacionCreateSerializer,
    MensajeSerializer, MensajeCreateSerializer, TransparenciaPreciosSerializer,
    TransparenciaPreciosCreateSerializer, CalculadoraAhorrosSerializer,
    ReporteImpactoSerializer, EstadisticasAntiIntermediariosSerializer
)


class IsParticipantOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para conversaciones: solo participantes pueden ver/editar
    """
    def has_object_permission(self, request, view, obj):
        # Solo participantes de la conversación pueden acceder
        return obj.campesino == request.user or obj.comprador == request.user


class ConversacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para conversaciones del sistema anti-intermediarios
    """
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activa', 'producto', 'campesino', 'comprador']
    search_fields = ['producto__nombre', 'campesino__nombre', 'comprador__nombre']
    ordering_fields = ['fecha_creacion', 'fecha_actualizacion']
    ordering = ['-fecha_actualizacion']

    def get_queryset(self):
        """Filtrar conversaciones del usuario autenticado"""
        user = self.request.user
        queryset = Conversacion.objects.select_related(
            'campesino', 'comprador', 'producto'
        ).prefetch_related('mensajes')
        
        # Mostrar solo conversaciones donde el usuario participa
        return queryset.filter(
            Q(campesino=user) | Q(comprador=user)
        )

    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'list':
            return ConversacionListSerializer
        elif self.action == 'retrieve':
            return ConversacionDetailSerializer
        elif self.action == 'create':
            return ConversacionCreateSerializer
        return ConversacionDetailSerializer

    def perform_create(self, serializer):
        """Personalizar creación de conversaciones"""
        # Validar que el usuario sea comprador
        if not self.request.user.tipo_usuario == 'comprador':
            raise permissions.PermissionDenied("Solo los compradores pueden iniciar conversaciones")
        
        serializer.save()

    @swagger_auto_schema(
        operation_description="Enviar mensaje en una conversación",
        request_body=MensajeCreateSerializer,
        responses={201: MensajeSerializer()}
    )
    @action(detail=True, methods=['post'])
    def enviar_mensaje(self, request, pk=None):
        """Enviar un mensaje en la conversación"""
        conversacion = self.get_object()
        
        # Verificar que el usuario participa en la conversación
        if request.user != conversacion.campesino and request.user != conversacion.comprador:
            return Response(
                {'error': 'No tienes permisos para enviar mensajes en esta conversación'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Crear mensaje
        serializer = MensajeCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.validated_data['conversacion'] = conversacion
            mensaje = serializer.save()
            
            # Actualizar fecha de actualización de la conversación
            conversacion.save()
            
            return Response(
                MensajeSerializer(mensaje).data, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Marcar mensajes como leídos",
        responses={200: openapi.Response("Mensajes marcados como leídos")}
    )
    @action(detail=True, methods=['patch'])
    def marcar_como_leidos(self, request, pk=None):
        """Marcar todos los mensajes de la conversación como leídos"""
        conversacion = self.get_object()
        
        # Marcar mensajes como leídos
        conversacion.marcar_mensajes_como_leidos(request.user)
        
        return Response({'message': 'Mensajes marcados como leídos'})

    @swagger_auto_schema(
        operation_description="Obtener mensajes de una conversación",
        responses={200: MensajeSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def mensajes(self, request, pk=None):
        """Obtener mensajes de una conversación"""
        conversacion = self.get_object()
        mensajes = conversacion.mensajes.all().order_by('fecha_envio')
        
        # Marcar mensajes como leídos al obtenerlos
        conversacion.marcar_mensajes_como_leidos(request.user)
        
        serializer = MensajeSerializer(mensajes, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Archivar/desarchivar conversación",
        responses={200: openapi.Response("Conversación actualizada")}
    )
    @action(detail=True, methods=['patch'])
    def toggle_activa(self, request, pk=None):
        """Archivar o desarchivar conversación"""
        conversacion = self.get_object()
        conversacion.activa = not conversacion.activa
        conversacion.save()
        
        estado = 'activada' if conversacion.activa else 'archivada'
        return Response({'message': f'Conversación {estado} correctamente'})


class TransparenciaPreciosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para transparencia de precios
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['producto', 'fuente_precio_referencia', 'ciudad_referencia']
    search_fields = ['producto__nombre', 'ciudad_referencia']
    ordering_fields = ['fecha_registro', 'ahorro_absoluto', 'ahorro_porcentual']
    ordering = ['-fecha_registro']

    def get_queryset(self):
        return TransparenciaPrecios.objects.select_related('producto').all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TransparenciaPreciosCreateSerializer
        return TransparenciaPreciosSerializer

    @swagger_auto_schema(
        operation_description="Calcular ahorros para una cantidad específica",
        request_body=CalculadoraAhorrosSerializer,
        responses={
            200: openapi.Response(
                "Cálculo de ahorros",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'producto': openapi.Schema(type=openapi.TYPE_STRING),
                        'cantidad': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'precio_campo_directo': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'precio_mercado': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'ahorro_total': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'ahorro_porcentual': openapi.Schema(type=openapi.TYPE_NUMBER),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['post'])
    def calculadora_ahorros(self, request):
        """Calculadora de ahorros por compra directa"""
        serializer = CalculadoraAhorrosSerializer(data=request.data)
        if serializer.is_valid():
            producto_id = serializer.validated_data['producto_id']
            cantidad = serializer.validated_data['cantidad']
            
            # Buscar comparación de precios más reciente
            try:
                transparencia = self.get_queryset().filter(
                    producto_id=producto_id
                ).latest('fecha_registro')
                
                # Calcular ahorros
                ahorro_total = transparencia.calcular_ahorro_por_cantidad(cantidad)
                
                return Response({
                    'producto': transparencia.producto.nombre,
                    'cantidad': cantidad,
                    'precio_campo_directo': transparencia.precio_campo_directo,
                    'precio_mercado': transparencia.precio_mercado_tradicional,
                    'costo_campo_directo': transparencia.precio_campo_directo * cantidad,
                    'costo_mercado': transparencia.precio_mercado_tradicional * cantidad,
                    'ahorro_total': ahorro_total,
                    'ahorro_porcentual': transparencia.ahorro_porcentual,
                    'fuente_referencia': transparencia.fuente_precio_referencia
                })
                
            except TransparenciaPrecios.DoesNotExist:
                return Response(
                    {'error': 'No hay datos de comparación de precios para este producto'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Obtener productos con mayores ahorros",
        responses={200: TransparenciaPreciosSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def mayores_ahorros(self, request):
        """Obtener productos con mayores ahorros"""
        queryset = self.get_queryset().filter(
            precio_campo_directo__lt=F('precio_mercado_tradicional')
        ).order_by('-ahorro_porcentual')[:10]
        
        serializer = TransparenciaPreciosSerializer(queryset, many=True)
        return Response(serializer.data)


class AntiIntermediariosStatsViewSet(viewsets.ViewSet):
    """
    ViewSet para estadísticas del sistema anti-intermediarios
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Obtener estadísticas generales del sistema anti-intermediarios",
        responses={200: EstadisticasAntiIntermediariosSerializer()}
    )
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales del sistema"""
        user = request.user
        
        # Estadísticas generales
        conversaciones_activas = Conversacion.objects.filter(activa=True).count()
        mensajes_totales = Mensaje.objects.count()
        
        # Ahorro promedio
        ahorro_promedio = TransparenciaPrecios.objects.filter(
            precio_campo_directo__lt=F('precio_mercado_tradicional')
        ).aggregate(promedio=Avg('ahorro_porcentual'))['promedio'] or 0
        
        productos_con_comparacion = TransparenciaPrecios.objects.values(
            'producto'
        ).distinct().count()
        
        # Estadísticas del usuario
        mis_conversaciones = Conversacion.objects.filter(
            Q(campesino=user) | Q(comprador=user)
        ).count()
        
        mensajes_enviados = Mensaje.objects.filter(remitente=user).count()
        mensajes_no_leidos = Mensaje.objects.filter(
            conversacion__in=Conversacion.objects.filter(
                Q(campesino=user) | Q(comprador=user)
            ),
            leido=False
        ).exclude(remitente=user).count()
        
        data = {
            'conversaciones_activas': conversaciones_activas,
            'mensajes_totales': mensajes_totales,
            'ahorro_promedio': round(ahorro_promedio, 2),
            'productos_con_comparacion': productos_con_comparacion,
            'mis_conversaciones': mis_conversaciones,
            'mensajes_enviados': mensajes_enviados,
            'mensajes_no_leidos': mensajes_no_leidos
        }
        
        serializer = EstadisticasAntiIntermediariosSerializer(data)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Generar reporte de impacto",
        manual_parameters=[
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, description="Fecha inicio (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('fecha_fin', openapi.IN_QUERY, description="Fecha fin (YYYY-MM-DD)", type=openapi.TYPE_STRING)
        ],
        responses={200: ReporteImpactoSerializer()}
    )
    @action(detail=False, methods=['post'])
    def generar_reporte_impacto(self, request):
        """Generar reporte de impacto del sistema"""
        fecha_inicio_str = request.query_params.get('fecha_inicio')
        fecha_fin_str = request.query_params.get('fecha_fin')
        
        if not fecha_inicio_str or not fecha_fin_str:
            return Response(
                {'error': 'Debe proporcionar fecha_inicio y fecha_fin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fecha_inicio = datetime.datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar reporte
        reporte = ReporteImpacto.generar_reporte(fecha_inicio, fecha_fin)
        serializer = ReporteImpactoSerializer(reporte)
        return Response(serializer.data)
