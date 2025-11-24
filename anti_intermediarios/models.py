"""
Modelos para funcionalidades Anti-Intermediarios de Campo Directo
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import datetime

Usuario = get_user_model()


class Conversacion(models.Model):
    """
    Conversación entre un campesino y un comprador
    """
    
    campesino = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='conversaciones_campesino',
        limit_choices_to={'tipo_usuario': 'campesino'}
    )
    
    comprador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='conversaciones_comprador',
        limit_choices_to={'tipo_usuario': 'comprador'}
    )
    
    # Producto sobre el que se conversa (opcional)
    producto = models.ForeignKey(
        'products.Producto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversaciones'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Estado de la conversación
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Conversación'
        verbose_name_plural = 'Conversaciones'
        unique_together = ('campesino', 'comprador', 'producto')
        indexes = [
            models.Index(fields=['campesino']),
            models.Index(fields=['comprador']),
            models.Index(fields=['fecha_actualizacion']),
        ]
    
    def __str__(self):
        producto_info = f" sobre {self.producto.nombre}" if self.producto else ""
        return f"Conversación: {self.campesino.get_full_name()} - {self.comprador.get_full_name()}{producto_info}"
    
    def ultimo_mensaje(self):
        """Obtiene el último mensaje de la conversación"""
        return self.mensajes.order_by('-fecha_envio').first()
    
    def mensajes_no_leidos_por_usuario(self, usuario):
        """Cuenta mensajes no leídos por un usuario"""
        return self.mensajes.filter(leido=False).exclude(remitente=usuario).count()
    
    def marcar_mensajes_como_leidos(self, usuario):
        """Marca todos los mensajes como leídos por un usuario"""
        self.mensajes.filter(leido=False).exclude(remitente=usuario).update(leido=True)


class Mensaje(models.Model):
    """
    Mensajes dentro de una conversación
    """
    
    TIPO_MENSAJE_CHOICES = [
        ('texto', 'Texto'),
        ('oferta', 'Oferta de Precio'),
        ('negociacion', 'Negociación'),
        ('sistema', 'Mensaje del Sistema'),
    ]
    
    conversacion = models.ForeignKey(
        Conversacion,
        on_delete=models.CASCADE,
        related_name='mensajes'
    )
    
    remitente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados'
    )
    
    tipo_mensaje = models.CharField(
        max_length=12,
        choices=TIPO_MENSAJE_CHOICES,
        default='texto'
    )
    
    contenido = models.TextField()
    
    # Para ofertas de precio
    precio_ofertado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    cantidad_ofertada = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        indexes = [
            models.Index(fields=['conversacion']),
            models.Index(fields=['fecha_envio']),
            models.Index(fields=['leido']),
        ]
        ordering = ['fecha_envio']
    
    def __str__(self):
        return f"Mensaje de {self.remitente.get_full_name()} - {self.fecha_envio}"
    
    @property
    def es_oferta(self):
        """Verifica si el mensaje es una oferta de precio"""
        return self.tipo_mensaje in ['oferta', 'negociacion']
    
    def marcar_como_leido(self):
        """Marca el mensaje como leído"""
        self.leido = True
        self.save()


class TransparenciaPrecios(models.Model):
    """
    Modelo para almacenar comparaciones de precios y transparencia
    """
    
    producto = models.ForeignKey(
        'products.Producto',
        on_delete=models.CASCADE,
        related_name='comparaciones_precio'
    )
    
    # Precio en Campo Directo (precio del campesino)
    precio_campo_directo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Precio de referencia del mercado (ej: SIPSA-DANE)
    precio_mercado_tradicional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Fuente del precio de referencia
    fuente_precio_referencia = models.CharField(
        max_length=100,
        default='SIPSA-DANE'
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    # Ubicación del precio de referencia
    ciudad_referencia = models.CharField(max_length=100, blank=True)
    
    # Notas adicionales
    notas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Transparencia de Precios'
        verbose_name_plural = 'Transparencia de Precios'
        indexes = [
            models.Index(fields=['producto']),
            models.Index(fields=['fecha_registro']),
        ]
    
    def __str__(self):
        return f"Comparación de {self.producto.nombre} - {self.fecha_registro.date()}"
    
    @property
    def ahorro_absoluto(self):
        """Calcula el ahorro absoluto"""
        return self.precio_mercado_tradicional - self.precio_campo_directo
    
    @property
    def ahorro_porcentual(self):
        """Calcula el ahorro porcentual"""
        if self.precio_mercado_tradicional > 0:
            return (self.ahorro_absoluto / self.precio_mercado_tradicional) * 100
        return 0
    
    @property
    def hay_ahorro(self):
        """Verifica si hay ahorro comprando directo"""
        return self.precio_campo_directo < self.precio_mercado_tradicional
    
    def calcular_ahorro_por_cantidad(self, cantidad):
        """Calcula el ahorro total para una cantidad específica"""
        return self.ahorro_absoluto * Decimal(str(cantidad))


class ReporteImpacto(models.Model):
    """
    Reportes de impacto de Campo Directo eliminando intermediarios
    """
    
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    # Estadísticas calculadas
    total_transacciones = models.PositiveIntegerField(default=0)
    ahorro_total_generado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    campesinos_beneficiados = models.PositiveIntegerField(default=0)
    compradores_beneficiados = models.PositiveIntegerField(default=0)
    
    # Productos más transados
    productos_top = models.JSONField(default=list, blank=True)
    
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Reporte de Impacto'
        verbose_name_plural = 'Reportes de Impacto'
        indexes = [
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
            models.Index(fields=['fecha_generacion']),
        ]
    
    def __str__(self):
        return f"Reporte {self.fecha_inicio} - {self.fecha_fin}"
    
    @classmethod
    def generar_reporte(cls, fecha_inicio, fecha_fin):
        """Genera un reporte de impacto para un período"""
        from django.db.models import Count, Sum
        from orders.models import Pedido
        
        # Obtener pedidos completados en el período
        pedidos = Pedido.objects.filter(
            estado='completed',
            fecha_completado__date__range=[fecha_inicio, fecha_fin]
        )
        
        # Calcular estadísticas
        total_transacciones = pedidos.count()
        
        campesinos = pedidos.values('campesino').distinct().count()
        compradores = pedidos.values('comprador').distinct().count()
        
        # Calcular ahorro total (necesitaría lógica más compleja con precios de referencia)
        ahorro_total = Decimal('0.00')  # Placeholder
        
        # Crear el reporte
        reporte = cls.objects.create(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            total_transacciones=total_transacciones,
            ahorro_total_generado=ahorro_total,
            campesinos_beneficiados=campesinos,
            compradores_beneficiados=compradores
        )
        
        return reporte
