"""
Modelos de Fincas para Campo Directo
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from utils.file_handlers import farm_image_handler, certificate_upload_handler, validate_image_file, validate_document_file
Usuario = get_user_model()


class Finca(models.Model):
    """
    Modelo para las fincas de los campesinos
    """
    
    TIPO_CULTIVO_CHOICES = [
        ('organico', 'Orgánico'),
        ('tradicional', 'Tradicional'),
        ('hidroponico', 'Hidropónico'),
        ('mixto', 'Mixto'),
    ]
    
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('en_revision', 'En Revisión'),
    ]
    
    # Relación con usuario campesino
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='fincas',
        limit_choices_to={'tipo_usuario': 'campesino'}
    )
    
    nombre_finca = models.CharField(max_length=150)
    ubicacion_departamento = models.CharField(max_length=100)
    ubicacion_municipio = models.CharField(max_length=100)
    direccion = models.TextField(blank=True)
    
    area_hectareas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Área de la finca en hectáreas'
    )
    
    tipo_cultivo = models.CharField(
        max_length=15,
        choices=TIPO_CULTIVO_CHOICES,
        default='organico'
    )
    
    descripcion = models.TextField(blank=True)
    
    # Coordenadas GPS
    latitud = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        help_text='Latitud GPS'
    )
    
    longitud = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        help_text='Longitud GPS'
    )
    
    estado = models.CharField(
        max_length=11,
        choices=ESTADO_CHOICES,
        default='activa'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Finca'
        verbose_name_plural = 'Fincas'
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['ubicacion_departamento', 'ubicacion_municipio']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"{self.nombre_finca} - {self.usuario.get_full_name()}"
    
    @property
    def ubicacion_completa(self):
        """Retorna la ubicación completa"""
        return f"{self.ubicacion_municipio}, {self.ubicacion_departamento}"
    
    @property
    def tiene_coordenadas(self):
        """Verifica si tiene coordenadas GPS"""
        return self.latitud is not None and self.longitud is not None
    
    def productos_count(self):
        """Cuenta los productos de esta finca"""
        return self.productos.count()
    
    def productos_disponibles_count(self):
        """Cuenta los productos disponibles de esta finca"""
        return self.productos.filter(estado='disponible').count()


