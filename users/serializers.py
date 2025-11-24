"""
Serializers para autenticación y gestión de usuarios
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import Usuario


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de usuarios
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    nombre_finca = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Solo para campesinos: nombre de la finca inicial'
    )

    class Meta:
        model = Usuario
        fields = [
            'email', 'password', 'password_confirm',
            'nombre', 'apellido', 'telefono', 'fecha_nacimiento',
            'tipo_usuario', 'nombre_finca'
        ]

    def validate(self, attrs):
        """Validaciones personalizadas"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        
        # Validar que el email no esté registrado
        if Usuario.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Este email ya está registrado")
            
        return attrs

    def create(self, validated_data):
        """Crear nuevo usuario"""
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        nombre_finca = validated_data.pop('nombre_finca', None)
        
        # Crear usuario
        user = Usuario.objects.create_user(password=password, **validated_data)
        
        # Si es campesino y tiene nombre de finca, crear finca
        if user.tipo_usuario == 'campesino' and nombre_finca:
            from farms.models import Finca
            Finca.objects.create(
                usuario=user,
                nombre_finca=nombre_finca,
                ubicacion_departamento='Por definir',
                ubicacion_municipio='Por definir',
                area_hectareas=0
            )
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login de usuarios
    """
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'No se pudo autenticar con las credenciales proporcionadas'
                )

            if not user.is_activo:
                raise serializers.ValidationError(
                    'La cuenta de usuario está deshabilitada'
                )

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Debe incluir email y contraseña'
            )


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer básico para información del usuario
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'apellido', 'full_name',
            'telefono', 'tipo_usuario', 'fecha_nacimiento',
            'estado', 'fecha_registro', 'calificacion_promedio',
            'total_calificaciones', 'avatar'
        ]
        read_only_fields = [
            'id', 'fecha_registro', 'calificacion_promedio',
            'total_calificaciones', 'estado'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar perfil de usuario
    """
    
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'telefono']
        
    def validate_telefono(self, value):
        """Validar formato del teléfono"""
        # El modelo ya tiene validación RegexValidator, pero podemos agregar lógica adicional
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambio de contraseña
    """
    current_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Las nuevas contraseñas no coinciden")
        return attrs

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta")
        return value


class UserDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer para dashboard del usuario con estadísticas
    """
    estadisticas = serializers.SerializerMethodField()
    finca_principal = serializers.SerializerMethodField()
    actividad_reciente = serializers.SerializerMethodField()
    # También exponer directamente los campos para el JS
    productos_activos = serializers.SerializerMethodField()
    pedidos_pendientes = serializers.SerializerMethodField()
    ventas_mes = serializers.SerializerMethodField()
    calificacion = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'email', 'tipo_usuario',
            'calificacion_promedio', 'total_calificaciones',
            'fecha_registro', 'estadisticas', 'finca_principal',
            'actividad_reciente', 'productos_activos', 'pedidos_pendientes',
            'ventas_mes', 'calificacion'
        ]
    
    def get_estadisticas(self, obj):
        """Obtener estadísticas completas del usuario para el dashboard"""
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta
        from decimal import Decimal
        
        stats = {}
        
        if obj.is_campesino:
            # Estadísticas de productos
            productos_activos = obj.productos.filter(estado='disponible').count()
            
            # Pedidos pendientes
            pedidos_pendientes = obj.pedidos_campesino.filter(
                estado__in=['pending', 'confirmed', 'preparing']
            ).count()
            
            # Ventas del mes actual
            inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            ventas_mes = obj.pedidos_campesino.filter(
                fecha_pedido__range=[inicio_mes, fin_mes],
                estado='completed'
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            
            # Productos vendidos en el mes
            productos_vendidos = obj.pedidos_campesino.filter(
                fecha_pedido__range=[inicio_mes, fin_mes],
                estado='completed'
            ).aggregate(total=Sum('detalles__cantidad'))['total'] or 0
            
            # Clientes únicos en el mes
            clientes_unicos = obj.pedidos_campesino.filter(
                fecha_pedido__range=[inicio_mes, fin_mes]
            ).values('comprador').distinct().count()
            
            stats.update({
                'productos_activos': productos_activos,
                'pedidos_pendientes': pedidos_pendientes,
                'ventas_mes': int(ventas_mes),
                'calificacion': float(obj.calificacion_promedio),
                'productos_vendidos': int(productos_vendidos),
                'clientes_unicos': clientes_unicos,
                'total_fincas': obj.fincas.count(),
                'fincas_activas': obj.fincas.filter(estado='activa').count(),
            })
            
        elif obj.is_comprador:
            # Período del mes actual
            inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            # Pedidos del mes
            pedidos_mes = obj.pedidos_comprador.filter(
                fecha_pedido__range=[inicio_mes, fin_mes]
            ).count()
            
            # Total gastado en el mes
            total_gastado = obj.pedidos_comprador.filter(
                fecha_pedido__range=[inicio_mes, fin_mes],
                estado__in=['completed', 'ready']
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            
            # Campesinos favoritos (estimación)
            campesinos_favoritos = obj.pedidos_comprador.values('campesino').distinct().count()
            
            # Ahorro estimado (15% vs precios de mercado)
            ahorro_estimado = total_gastado * Decimal('0.15')
            
            # Pedidos activos
            pedidos_activos = obj.pedidos_comprador.filter(
                estado__in=['pending', 'confirmed', 'preparing', 'ready']
            ).count()
            
            stats.update({
                'pedidos_mes': pedidos_mes,
                'total_gastado': int(total_gastado),
                'campesinos_favoritos': campesinos_favoritos,
                'ahorro_total': int(ahorro_estimado),
                'pedidos_activos': pedidos_activos,
            })
            
        return stats
    
    def get_finca_principal(self, obj):
        """Obtener información de la finca principal (solo para campesinos)"""
        if obj.is_campesino:
            finca = obj.get_finca_principal()
            if finca:
                return {
                    'id': finca.id,
                    'nombre': finca.nombre_finca,
                    'ubicacion': finca.ubicacion_completa,
                    'area_hectareas': finca.area_hectareas,
                    'tipo_cultivo': finca.get_tipo_cultivo_display()
                }
        return None
    
    # Métodos para campos directos (para compatibilidad con JS)
    def get_productos_activos(self, obj):
        if obj.is_campesino:
            return obj.productos.filter(estado='disponible').count()
        return 0
        
    def get_pedidos_pendientes(self, obj):
        if obj.is_campesino:
            return obj.pedidos_campesino.filter(
                estado__in=['pending', 'confirmed', 'preparing']
            ).count()
        elif obj.is_comprador:
            return obj.pedidos_comprador.filter(
                estado__in=['pending', 'confirmed', 'preparing', 'ready']
            ).count()
        return 0
        
    def get_ventas_mes(self, obj):
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import timedelta
        from decimal import Decimal
        
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        if obj.is_campesino:
            ventas = obj.pedidos_campesino.filter(
                fecha_pedido__range=[inicio_mes, fin_mes],
                estado='completed'
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            return int(ventas)
        return 0
        
    def get_calificacion(self, obj):
        return float(obj.calificacion_promedio)
        
    def get_actividad_reciente(self, obj):
        """Obtener actividad reciente del usuario"""
        from django.utils import timezone
        
        actividades = []
        
        if obj.is_campesino:
            # Obtener últimos 5 pedidos como campesino
            pedidos_recientes = obj.pedidos_campesino.order_by('-fecha_pedido')[:5]
            
            for pedido in pedidos_recientes:
                tiempo_transcurrido = timezone.now() - pedido.fecha_pedido
                
                if tiempo_transcurrido.days == 0:
                    if tiempo_transcurrido.seconds < 3600:
                        tiempo = f"Hace {tiempo_transcurrido.seconds // 60} minutos"
                    else:
                        tiempo = f"Hace {tiempo_transcurrido.seconds // 3600} horas"
                else:
                    tiempo = f"Hace {tiempo_transcurrido.days} día{'s' if tiempo_transcurrido.days > 1 else ''}"
                
                actividades.append({
                    'tipo': 'pedido',
                    'descripcion': f"Pedido {pedido.get_estado_display().lower()} - {pedido.comprador.get_full_name()}",
                    'tiempo': tiempo,
                    'estado': pedido.estado
                })
                
        elif obj.is_comprador:
            # Obtener últimos 5 pedidos como comprador
            pedidos_recientes = obj.pedidos_comprador.order_by('-fecha_pedido')[:5]
            
            for pedido in pedidos_recientes:
                tiempo_transcurrido = timezone.now() - pedido.fecha_pedido
                
                if tiempo_transcurrido.days == 0:
                    if tiempo_transcurrido.seconds < 3600:
                        tiempo = f"Hace {tiempo_transcurrido.seconds // 60} minutos"
                    else:
                        tiempo = f"Hace {tiempo_transcurrido.seconds // 3600} horas"
                else:
                    tiempo = f"Hace {tiempo_transcurrido.days} día{'s' if tiempo_transcurrido.days > 1 else ''}"
                
                actividades.append({
                    'tipo': 'pedido',
                    'descripcion': f"Pedido {pedido.get_estado_display().lower()} - {pedido.campesino.get_full_name()}",
                    'tiempo': tiempo,
                    'estado': pedido.estado,
                    'total': float(pedido.total)
                })
                
        return actividades
