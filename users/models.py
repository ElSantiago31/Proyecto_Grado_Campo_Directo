"""
Modelos de Usuario para Campo Directo
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from utils.file_handlers import profile_image_handler, validate_image_file
from decimal import Decimal


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario
    """
    def create_user(self, email, password=None, **extra_fields):
        """Crear usuario normal"""
        if not email:
            raise ValueError('El usuario debe tener un email')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Crear superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_usuario', 'comprador')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
            
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    """
    Modelo de Usuario personalizado para Campo Directo
    Reemplaza el modelo User de Django por defecto
    """
    
    TIPO_USUARIO_CHOICES = [
        ('campesino', 'Campesino'),
        ('comprador', 'Comprador'),
    ]
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('suspendido', 'Suspendido'),
    ]
    
    # Remover campos de AbstractUser que no necesitamos
    username = None
    first_name = None
    last_name = None
    
    # Campos personalizados
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    
    # Validador para teléfono colombiano (más flexible)
    phone_validator = RegexValidator(
        regex=r'^(\+57|57)?[0-9]{10}$',
        message="Número de teléfono debe tener 10 dígitos (formato colombiano)"
    )
    telefono = models.CharField(
        max_length=20,
        validators=[phone_validator],
        help_text='Formato: 10 dígitos (ej: 3001234567)'
    )
    
    tipo_usuario = models.CharField(
        max_length=10,
        choices=TIPO_USUARIO_CHOICES,
        default='campesino'
    )
    
    # Campo de dirección agregado posterior para los compradores principalmente
    direccion = models.CharField(
        max_length=255, 
        blank=True, 
        help_text='Dirección obligatoria para compradores (Opcional para Campesinos)'
    )
    
    fecha_nacimiento = models.DateField()
    
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='activo'
    )
    
    # Campo 2FA Visual inclusivo
    imagen_2fa = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Emoji secreto para Autenticación Basada en Reconocimiento (2FA)'
    )
    intentos_2fa_fallidos = models.PositiveSmallIntegerField(
        default=0,
        help_text='Contador de intentos fallidos del PIN Visual'
    )
    bloqueado_2fa_hasta = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha/hora hasta la que está bloqueado el 2FA por intentos excesivos'
    )
    intentos_password_fallidos = models.PositiveSmallIntegerField(
        default=0,
        help_text='Contador de intentos fallidos de contraseña'
    )
    bloqueado_password_hasta = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha/hora hasta la que está bloqueada la cuenta por contraseña incorrecta repetida'
    )
    
    suspendido_hasta = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha y hora hasta la cual el usuario está sancionado. Si es nulo y el estado es Suspendido, es permanente.'
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    ultimo_login = models.DateTimeField(null=True, blank=True)
    
    # Imagen de perfil
    avatar = models.ImageField(
        upload_to=profile_image_handler,
        null=True,
        blank=True,
        validators=[validate_image_file],
        help_text='Imagen de perfil del usuario (máx. 5MB, formatos: JPG, PNG, GIF, WebP)'
    )
    
    # Sistema de calificaciones
    calificacion_promedio = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=Decimal('0.0'),
        help_text='Calificación promedio del usuario'
    )
    
    total_calificaciones = models.PositiveIntegerField(
        default=0,
        help_text='Número total de calificaciones recibidas'
    )
    
    # Configuración para usar email como username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'telefono', 'fecha_nacimiento', 'tipo_usuario']
    
    objects = UsuarioManager()
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['tipo_usuario']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.email})"
    
    def get_full_name(self):
        """Retorna el nombre completo"""
        return f"{self.nombre} {self.apellido}".strip()
    
    def get_short_name(self):
        """Retorna el nombre corto"""
        return self.nombre
    
    @property
    def is_campesino(self):
        """Verifica si el usuario es campesino"""
        return self.tipo_usuario == 'campesino'
    
    @property
    def is_comprador(self):
        """Verifica si el usuario es comprador"""
        return self.tipo_usuario == 'comprador'
    
    @property
    def is_activo(self):
        """
        Verifica si el usuario está activo y no tiene sanciones vigentes.
        """
        if self.estado == 'suspendido':
            if self.suspendido_hasta:
                from django.utils import timezone
                if timezone.now() < self.suspendido_hasta:
                    return False # Sigue sancionado
                # Si la fecha ya pasó, el usuario está virtualmente activo
                return True
            return False # Suspensión permanente
        return self.estado == 'activo' and self.is_active
    
    def actualizar_calificacion(self, nueva_calificacion):
        """
        Actualiza la calificación promedio del usuario
        """
        total_puntos = (self.calificacion_promedio * self.total_calificaciones) + nueva_calificacion
        self.total_calificaciones += 1
        self.calificacion_promedio = total_puntos / self.total_calificaciones
        self.save()
    
    def tiene_finca(self):
        """
        Verifica si el usuario campesino tiene al menos una finca
        """
        if not self.is_campesino:
            return False
        return self.fincas.exists()
    
    def get_finca_principal(self):
        """
        Obtiene la finca principal del campesino (la primera creada)
        """
        if not self.is_campesino:
            return None
        return self.fincas.filter(estado='activa').first()
    
    def puede_crear_productos(self):
        """
        Verifica si el usuario puede crear productos
        """
        return self.is_campesino and self.is_activo and self.tiene_finca()
    
    def productos_disponibles_count(self):
        """
        Cuenta los productos disponibles del campesino
        """
        if not self.is_campesino:
            return 0
        return self.productos.filter(estado='disponible').count()
    
    def pedidos_como_comprador_count(self):
        """
        Cuenta los pedidos realizados como comprador
        """
        if not self.is_comprador:
            return 0
        return self.pedidos_comprador.count()
    
    def pedidos_como_campesino_count(self):
        """
        Cuenta los pedidos recibidos como campesino
        """
        if not self.is_campesino:
            return 0
        return self.pedidos_campesino.count()

    def save(self, *args, **kwargs):
        """
        Mantenemos is_active=True por defecto para permitir que el login intercepte
        al usuario y le muestre un mensaje de "Estás suspendido" en lugar de uno genérico.
        Solo se pone False si el estado es 'inactivo' permanentemente.
        """
        if self.estado == 'inactivo':
            self.is_active = False
        else:
            self.is_active = True
        super().save(*args, **kwargs)
