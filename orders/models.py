"""
Modelos de Pedidos para Campo Directo
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from datetime import datetime

Usuario = get_user_model()


class Pedido(models.Model):
    """
    Modelo de pedidos/órdenes de compra
    """
    
    ESTADO_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('preparing', 'En Preparación'),
        ('ready', 'Listo para Entrega'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('otro', 'Otro'),
    ]
    
    # ID personalizado formato: ORD-XXXXX
    id = models.CharField(
        max_length=20,
        primary_key=True,
        editable=False,
        help_text='Formato: ORD-XXXXX'
    )
    
    # Relaciones
    comprador = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        related_name='pedidos_comprador',
        limit_choices_to={'tipo_usuario': 'comprador'}
    )
    
    campesino = models.ForeignKey(
        Usuario,
        on_delete=models.RESTRICT,
        related_name='pedidos_campesino',
        limit_choices_to={'tipo_usuario': 'campesino'}
    )
    
    # Información del pedido
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='pending'
    )
    
    metodo_pago = models.CharField(
        max_length=15,
        choices=METODO_PAGO_CHOICES,
        default='efectivo'
    )
    
    # Notas
    notas_comprador = models.TextField(blank=True)
    notas_campesino = models.TextField(blank=True)
    
    # Fechas de seguimiento
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    fecha_preparacion = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    # Información de entrega
    direccion_entrega = models.TextField(blank=True)
    telefono_contacto = models.CharField(max_length=20, blank=True)
    fecha_entrega_programada = models.DateField(null=True, blank=True)
    hora_entrega_programada = models.TimeField(null=True, blank=True)
    
    # Seguimiento
    codigo_seguimiento = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )
    
    # Calificaciones
    calificacion_comprador = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Calificación del comprador al campesino'
    )
    
    calificacion_campesino = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Calificación del campesino al comprador'
    )
    
    comentario_calificacion = models.TextField(blank=True)
    
    # ─── MÓDULO PRUEBA DE PAGO (Local - No subir al repositorio) ─────────────
    # Permite al comprador subir el screenshot del comprobante Nequi/Transfencia
    # y al campesino confirmarlo, eliminando la necesidad de una pasarela de pagos.
    comprobante_pago = models.ImageField(
        upload_to='comprobantes_pago/',
        null=True,
        blank=True,
        help_text='Screenshot del comprobante Nequi o transferencia bancaria'
    )
    pago_confirmado_campesino = models.BooleanField(
        default=False,
        help_text='El campesino confirmó haber recibido el pago antes de despachar'
    )
    fecha_confirmacion_pago = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora en que el campesino aceptó el comprobante'
    )
    disputa_abierta = models.BooleanField(
        default=False,
        help_text='True si alguna de las partes reportó un problema con este pedido'
    )
    motivo_disputa = models.TextField(
        blank=True,
        help_text='Descripción del problema reportado por comprador o campesino'
    )
    # ─────────────────────────────────────────────────────────────────────────

    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_pedido']
        indexes = [
            models.Index(fields=['comprador']),
            models.Index(fields=['campesino']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_pedido']),
            models.Index(fields=['codigo_seguimiento']),
        ]
    
    def __str__(self):
        return f"{self.id} - {self.comprador.get_full_name()} -> {self.campesino.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generar un ID numérico corto (a partir de 1000) en formato string
            # Esto mantiene la integridad de la base de datos sin necesitar migraciones
            contador = Pedido.objects.count()
            base_id = 1000 + contador + 1
            
            nuevo_id = str(base_id)
            # Garantizar unicidad
            while Pedido.objects.filter(id=nuevo_id).exists():
                base_id += 1
                nuevo_id = str(base_id)
                
            self.id = nuevo_id
            
        if not self.codigo_seguimiento:
            # Generar código de seguimiento
            self.codigo_seguimiento = f"TRK-{uuid.uuid4().hex[:10].upper()}"
            
        super().save(*args, **kwargs)
    
    @property
    def estado_display_color(self):
        """Retorna un color para mostrar el estado"""
        colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'preparing': 'primary',
            'ready': 'success',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return colors.get(self.estado, 'secondary')
    
    def puede_ser_cancelado(self):
        """Verifica si el pedido puede ser cancelado"""
        return self.estado in ['pending', 'confirmed']
    
    def puede_ser_calificado_por_comprador(self):
        """Verifica si el comprador puede calificar"""
        return self.estado == 'completed' and not self.calificacion_comprador
    
    def puede_ser_calificado_por_campesino(self):
        """Verifica si el campesino puede calificar"""
        return self.estado == 'completed' and not self.calificacion_campesino
    
    def actualizar_estado(self, nuevo_estado, usuario=None):
        """Actualiza el estado del pedido y registra timestamps"""
        from django.utils import timezone
        
        if nuevo_estado == 'confirmed' and not self.fecha_confirmacion:
            self.fecha_confirmacion = timezone.now()
        elif nuevo_estado == 'preparing' and not self.fecha_preparacion:
            self.fecha_preparacion = timezone.now()
        elif nuevo_estado == 'completed' and not self.fecha_completado:
            self.fecha_completado = timezone.now()
            
        # Si se cancela el pedido, restaurar el stock automáticamente
        if nuevo_estado == 'cancelled' and self.estado != 'cancelled':
            for detalle in self.detalles.all():
                detalle.producto.aumentar_stock(int(detalle.cantidad))
                
        self.estado = nuevo_estado
        self.save()
    
    def calcular_total_desde_detalles(self):
        """Calcula el total basado en los detalles del pedido"""
        total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.total = total
        self.save()
        return total
    
    def get_productos_resumen(self):
        """Obtiene un resumen de los productos del pedido"""
        return [
            {
                'producto': detalle.producto.nombre,
                'cantidad': detalle.cantidad,
                'precio_unitario': detalle.precio_unitario,
                'subtotal': detalle.subtotal
            }
            for detalle in self.detalles.all()
        ]


class DetallePedido(models.Model):
    """
    Detalle de productos en cada pedido
    """
    
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    
    producto = models.ForeignKey(
        'products.Producto',
        on_delete=models.PROTECT,
        related_name='detalles_pedido'
    )
    
    cantidad = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Precio por unidad al momento del pedido'
    )
    
    # Información adicional capturada al momento del pedido
    nombre_producto_snapshot = models.CharField(
        max_length=150,
        help_text='Nombre del producto al momento del pedido'
    )
    
    unidad_medida_snapshot = models.CharField(
        max_length=7,
        help_text='Unidad de medida al momento del pedido'
    )
    
    class Meta:
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedidos'
        unique_together = ('pedido', 'producto')
    
    def __str__(self):
        return f"{self.pedido.id} - {self.producto.nombre}"
    
    @property
    def subtotal(self):
        """Calcula el subtotal de este detalle"""
        return self.cantidad * self.precio_unitario
    
    def save(self, *args, **kwargs):
        # Capturar snapshot del producto
        if self.producto:
            self.nombre_producto_snapshot = self.producto.nombre
            self.unidad_medida_snapshot = self.producto.unidad_medida
            
            # Si no se especificó precio, usar el actual del producto
            if not self.precio_unitario:
                self.precio_unitario = self.producto.precio_por_kg
                
        super().save(*args, **kwargs)
