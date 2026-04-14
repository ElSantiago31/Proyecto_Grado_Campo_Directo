"""
Modelos de Productos para Campo Directo
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json
import io
from PIL import Image as PilImage
from django.core.files.base import ContentFile
from users.models import Usuario
from utils.file_handlers import image_upload_handler, validate_image_file

class SipsaPrecio(models.Model):
    """
    Caché local de precios oficiales del Mercado Mayorista SIPSA del DANE.
    Se actualiza periódicamente vía comando cron.
    """
    ciudad = models.CharField(max_length=150)
    producto = models.CharField(max_length=200)
    precio_promedio = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_captura = models.DateTimeField(null=True, blank=True)
    ultima_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Precio SIPSA'
        verbose_name_plural = 'Precios SIPSA'
        indexes = [
            models.Index(fields=['producto']),
            models.Index(fields=['ciudad']),
        ]
        unique_together = ('ciudad', 'producto')

    def __str__(self):
        return f"{self.producto} en {self.ciudad} - ${self.precio_promedio}"

Usuario = get_user_model()


class CategoriaProducto(models.Model):
    """
    Categorías de productos agrícolas
    """
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=50, default='🌱')  # Emoji por defecto
    estado = models.CharField(
        max_length=8,
        choices=ESTADO_CHOICES,
        default='activo'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoría de Producto'
        verbose_name_plural = 'Categorías de Productos'
    
    def __str__(self):
        return self.nombre
    
    def productos_count(self):
        """Cuenta los productos en esta categoría"""
        return self.productos.filter(estado='disponible').count()


class Producto(models.Model):
    """
    Modelo de productos de los campesinos
    """
    
    UNIDAD_MEDIDA_CHOICES = [
        ('kg', 'Kilogramo (Kg)'),
        ('libra', 'Libra'),
        ('arroba', 'Arroba'),
        ('gramo', 'Gramo'),
        ('bulto', 'Bulto'),
        ('caja', 'Caja'),
        ('canasta', 'Canasta'),
        ('unidad', 'Unidad (Ej: Pollo)'),
    ]
    
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('agotado', 'Agotado'),
        ('temporada', 'Fuera de Temporada'),
        ('inactivo', 'Inactivo'),
    ]
    
    CALIDAD_CHOICES = [
        ('premium', 'Premium'),
        ('primera', 'Primera'),
        ('segunda', 'Segunda'),
    ]
    
    # Relaciones
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='productos',
        limit_choices_to={'tipo_usuario': 'campesino'}
    )
    
    finca = models.ForeignKey(
        'farms.Finca',
        on_delete=models.CASCADE,
        related_name='productos'
    )
    
    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.PROTECT,
        related_name='productos'
    )
    
    # Información básica
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    
    # Precio y stock
    precio_por_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    stock_disponible = models.PositiveIntegerField(default=0)
    
    unidad_medida = models.CharField(
        max_length=7,
        choices=UNIDAD_MEDIDA_CHOICES,
        default='kg'
    )
    
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='disponible'
    )
    
    # Imágenes
    imagen_principal = models.ImageField(
        upload_to=image_upload_handler,
        null=True,
        blank=True,
        validators=[validate_image_file],
        help_text='Imagen principal del producto (máx. 5MB, formatos: JPG, PNG, GIF, WebP)'
    )
    
    # Galeria de imágenes almacenada como JSON
    galeria_imagenes = models.JSONField(
        default=list,
        blank=True,
        help_text='Array de URLs de imágenes adicionales'
    )
    
    # Tags para búsquedas
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text='Palabras clave separadas por comas: orgánico, fresco, etc.'
    )
    
    # Información de calidad
    calidad = models.CharField(
        max_length=8,
        choices=CALIDAD_CHOICES,
        default='primera'
    )
    
    # Fechas importantes
    fecha_cosecha = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    
    # Límites de venta
    peso_minimo_venta = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.5'),
        validators=[MinValueValidator(Decimal('0.1'))]
    )
    
    peso_maximo_venta = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('100.0'),
        validators=[MinValueValidator(Decimal('0.5'))]
    )
    
    # Disponibilidad
    disponible_entrega_inmediata = models.BooleanField(
        default=True,
        help_text='¿Está disponible para entrega inmediata?'
    )
    
    tiempo_preparacion_dias = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text='Días necesarios para preparar el pedido'
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['categoria']),
            models.Index(fields=['estado']),
            models.Index(fields=['precio_por_kg']),
            models.Index(fields=['stock_disponible']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.usuario.get_full_name()}"

    def save(self, *args, **kwargs):
        """
        Comprime y convierte la imagen_principal a WebP al guardar.
        Reduce el tamaño de ~2MB a ~40KB automaticamente.
        """
        if self.imagen_principal:
            try:
                img = PilImage.open(self.imagen_principal)

                # Conservar modo RGBA para transparencias, sino RGB
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')

                # Solo redimensionar si es más grande que 800x800
                max_size = (800, 800)
                img.thumbnail(max_size, PilImage.LANCZOS)

                # Guardar en memoria como WebP
                buffer = io.BytesIO()
                save_format = 'WEBP'
                img.save(buffer, format=save_format, quality=85, optimize=True)
                buffer.seek(0)

                # Reemplazar el archivo con el WebP comprimido
                nombre_sin_ext = self.imagen_principal.name.rsplit('.', 1)[0]
                nuevo_nombre = f"{nombre_sin_ext.split('/')[-1]}.webp"
                self.imagen_principal.save(
                    nuevo_nombre,
                    ContentFile(buffer.read()),
                    save=False  # evitar recursion
                )
            except Exception:
                pass  # Si falla la compresion, guarda la imagen original sin romper el flujo

        super().save(*args, **kwargs)
    
    @property
    def is_disponible(self):
        """Verifica si el producto está disponible"""
        return self.estado == 'disponible' and self.stock_disponible > 0
    
    @property
    def precio_formateado(self):
        """Retorna el precio formateado"""
        return f"${self.precio_por_kg:,.0f} por {self.unidad_medida}"
    
    def get_tags_list(self):
        """Convierte los tags en una lista"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def set_tags_from_list(self, tags_list):
        """Establece los tags desde una lista"""
        if isinstance(tags_list, list):
            self.tags = ', '.join(tags_list)
        else:
            self.tags = str(tags_list)
    
    def get_galeria_urls(self):
        """Obtiene las URLs de la galería"""
        if isinstance(self.galeria_imagenes, str):
            try:
                return json.loads(self.galeria_imagenes)
            except json.JSONDecodeError:
                return []
        return self.galeria_imagenes or []
    
    def add_imagen_galeria(self, url):
        """Agrega una imagen a la galería"""
        imagenes = self.get_galeria_urls()
        if url not in imagenes:
            imagenes.append(url)
            self.galeria_imagenes = imagenes
            self.save()
    
    def remove_imagen_galeria(self, url):
        """Elimina una imagen de la galería"""
        imagenes = self.get_galeria_urls()
        if url in imagenes:
            imagenes.remove(url)
            self.galeria_imagenes = imagenes
            self.save()
    
    def puede_ser_comprado_por_cantidad(self, cantidad):
        """Verifica si se puede comprar la cantidad especificada"""
        if not self.is_disponible:
            return False, "Producto no disponible"
        
        if cantidad < self.peso_minimo_venta:
            return False, f"Cantidad mínima: {self.peso_minimo_venta} {self.unidad_medida}"
        
        # Omitimos el límite de venta máximo para permitir pedidos al por mayor
        # siempre y cuando el stock lo resista.
        
        if cantidad > self.stock_disponible:
            return False, f"Stock insuficiente. Disponible: {self.stock_disponible} {self.unidad_medida}"
        
        return True, "OK"
    
    def calcular_precio_total(self, cantidad):
        """Calcula el precio total para una cantidad"""
        return self.precio_por_kg * Decimal(str(cantidad))
    
    def reducir_stock(self, cantidad):
        """Reduce el stock del producto"""
        if cantidad <= self.stock_disponible:
            self.stock_disponible -= int(cantidad)
            if self.stock_disponible == 0:
                self.estado = 'agotado'
            self.save()
        else:
            raise ValueError("Stock insuficiente")
    
    def aumentar_stock(self, cantidad):
        """Aumenta el stock del producto"""
        self.stock_disponible += int(cantidad)
        if self.estado == 'agotado':
            self.estado = 'disponible'
        self.save()
