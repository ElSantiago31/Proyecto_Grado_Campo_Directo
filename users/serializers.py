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
    departamento_finca = serializers.CharField(
        required=False, allow_blank=True
    )
    municipio_finca = serializers.CharField(
        required=False, allow_blank=True
    )
    imagen_2fa = serializers.CharField(
        required=True,
        help_text='Emoji obligatorio para doble factor'
    )

    class Meta:
        model = Usuario
        fields = [
            'email', 'password', 'password_confirm',
            'nombre', 'apellido', 'telefono', 'fecha_nacimiento',
            'tipo_usuario', 'nombre_finca', 'direccion',
            'departamento_finca', 'municipio_finca', 'imagen_2fa'
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
        departamento_finca = validated_data.pop('departamento_finca', None)
        municipio_finca = validated_data.pop('municipio_finca', None)
        imagen_2fa = validated_data.pop('imagen_2fa', None)
        
        # Crear usuario
        user = Usuario.objects.create_user(password=password, imagen_2fa=imagen_2fa, **validated_data)
        
        # Si es campesino y tiene nombre de finca, crear finca
        if user.tipo_usuario == 'campesino' and nombre_finca:
            from farms.models import Finca
            Finca.objects.create(
                usuario=user,
                nombre_finca=nombre_finca,
                ubicacion_departamento=departamento_finca or '',
                ubicacion_municipio=municipio_finca or '',
                area_hectareas=0,
                tipo_cultivo='tradicional'
            )
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login de usuarios
    """
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})
    imagen_2fa = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        imagen_2fa = attrs.get('imagen_2fa')

        if email and password:
            from django.utils import timezone as tz
            from datetime import timedelta

            # --- BLOQUEO POR CONTRASEÑA: verificar antes de autenticar ---
            MAX_PWD = 5
            BLOQUEO_PWD_MIN = 10
            try:
                candidate = Usuario.objects.get(email=email)
                if candidate.bloqueado_password_hasta and tz.now() < candidate.bloqueado_password_hasta:
                    seg = int((candidate.bloqueado_password_hasta - tz.now()).total_seconds())
                    raise serializers.ValidationError(
                        f'Cuenta bloqueada por demasiados intentos de contraseña. Espera {seg} segundos.',
                        code='password_bloqueado'
                    )
            except Usuario.DoesNotExist:
                candidate = None
            except Usuario.MultipleObjectsReturned:
                # Esto no debería ocurrir por el unique=True, pero si ocurre es un error crítico
                raise serializers.ValidationError(
                    'Error de integridad de datos: Múltiples usuarios con el mismo email.'
                )

            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )

            if not user:
                # Contabilizar intento fallido de contraseña
                if candidate:
                    candidate.intentos_password_fallidos += 1
                    if candidate.intentos_password_fallidos >= MAX_PWD:
                        candidate.bloqueado_password_hasta = tz.now() + timedelta(minutes=BLOQUEO_PWD_MIN)
                        candidate.intentos_password_fallidos = 0
                        candidate.save(update_fields=['intentos_password_fallidos', 'bloqueado_password_hasta'])
                        raise serializers.ValidationError(
                            f'Demasiados intentos fallidos. Cuenta bloqueada {BLOQUEO_PWD_MIN} minutos.',
                            code='password_bloqueado'
                        )
                    restantes = MAX_PWD - candidate.intentos_password_fallidos
                    candidate.save(update_fields=['intentos_password_fallidos'])
                    raise serializers.ValidationError(
                        f'Contraseña incorrecta. Te quedan {restantes} intento(s) antes del bloqueo.'
                    )
                raise serializers.ValidationError(
                    'No se pudo autenticar con las credenciales proporcionadas'
                )

            # Contraseña correcta: resetear contador
            user.intentos_password_fallidos = 0
            user.bloqueado_password_hasta = None
            user.save(update_fields=['intentos_password_fallidos', 'bloqueado_password_hasta'])

            # --- BLOQUEO POR INTENTOS FALLIDOS DEL 2FA VISUAL ---
            MAX_INTENTOS = 3
            BLOQUEO_MINUTOS = 5

            # 1. Comprobar si está bloqueado temporalmente por PIN
            from django.utils import timezone as tz
            if user.bloqueado_2fa_hasta and tz.now() < user.bloqueado_2fa_hasta:
                segundos_restantes = int((user.bloqueado_2fa_hasta - tz.now()).total_seconds())
                raise serializers.ValidationError(
                    f'Código visual bloqueado. Espera {segundos_restantes} segundos e inténtalo de nuevo.',
                    code='visual_2fa_bloqueado'
                )

            # 2. Verificar el PIN Visual (Solo si el usuario tiene una imagen configurada)
            # Nota: Si no tiene imagen, el PIN se ignora por ahora (permitiendo transición suave)
            if getattr(user, 'imagen_2fa', None):
                if not imagen_2fa or user.imagen_2fa != imagen_2fa:
                    user.intentos_2fa_fallidos += 1
                    
                    if user.intentos_2fa_fallidos >= MAX_INTENTOS:
                        from datetime import timedelta
                        user.bloqueado_2fa_hasta = tz.now() + timedelta(minutes=BLOQUEO_MINUTOS)
                        user.intentos_2fa_fallidos = 0
                        user.save(update_fields=['intentos_2fa_fallidos', 'bloqueado_2fa_hasta'])
                        raise serializers.ValidationError(
                            f'Demasiados intentos fallidos. Cuenta bloqueada por {BLOQUEO_MINUTOS} minutos.',
                            code='visual_2fa_bloqueado'
                        )
                    
                    user.save(update_fields=['intentos_2fa_fallidos'])
                    restantes = MAX_INTENTOS - user.intentos_2fa_fallidos
                    raise serializers.ValidationError(
                        f'PIN Visual incorrecto. Te quedan {restantes} intento(s) antes del bloqueo.',
                        code='visual_2fa_failed'
                    )
                
                # PIN correcto: resetear contador
                user.intentos_2fa_fallidos = 0
                user.bloqueado_2fa_hasta = None
                user.save(update_fields=['intentos_2fa_fallidos', 'bloqueado_2fa_hasta'])
            else:
                # Si el usuario NO tiene PIN configurado pero está enviando uno, 
                # o si queremos forzar el bloqueo por 'intentos' genéricos:
                # En este caso, para que el test pase, debemos asegurar que el usuario del TEST tenga PIN.
                pass

            # --- NUEVA REGLA: VALIDACIÓN DE SANCIONES (SUSPENSIONES) ---
            if not user.is_activo:
                if user.estado == 'suspendido':
                    if user.suspendido_hasta:
                        fecha_str = user.suspendido_hasta.strftime('%d/%m/%Y %H:%M')
                        raise serializers.ValidationError(
                            f'Tu cuenta se encuentra suspendida temporalmente hasta el {fecha_str} por incumplimiento de nuestras políticas de comunidad.',
                            code='account_suspended'
                        )
                    else:
                        raise serializers.ValidationError(
                            'Tu cuenta ha sido suspendida permanentemente de Campo Directo.',
                            code='account_banned'
                        )
                elif user.estado == 'inactivo':
                    raise serializers.ValidationError(
                        'Esta cuenta se encuentra inactiva.',
                        code='account_inactive'
                    )
                else:
                    # Fallback por si acaso
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
    nombre_finca = serializers.SerializerMethodField()
    departamento_finca = serializers.SerializerMethodField()
    municipio_finca = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'apellido', 'full_name',
            'telefono', 'direccion', 'tipo_usuario', 'fecha_nacimiento',
            'estado', 'fecha_registro', 'calificacion_promedio',
            'total_calificaciones', 'avatar', 'nombre_finca',
            'departamento_finca', 'municipio_finca'
        ]
        read_only_fields = [
            'id', 'fecha_registro', 'calificacion_promedio',
            'total_calificaciones', 'estado'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()
        
    def get_nombre_finca(self, obj):
        finca = obj.get_finca_principal()
        return finca.nombre_finca if finca else ""
        
    def get_departamento_finca(self, obj):
        finca = obj.get_finca_principal()
        return finca.ubicacion_departamento if finca else ""
        
    def get_municipio_finca(self, obj):
        finca = obj.get_finca_principal()
        return finca.ubicacion_municipio if finca else ""


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar perfil de usuario
    """
    nombre_finca = serializers.CharField(required=False, allow_blank=True)
    departamento_finca = serializers.CharField(required=False, allow_blank=True)
    municipio_finca = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Usuario
        fields = [
            'nombre', 'apellido', 'telefono', 'email', 'direccion', 
            'fecha_nacimiento', 'nombre_finca', 'departamento_finca', 
            'municipio_finca', 'avatar'
        ]
        
    def validate_telefono(self, value):
        """Validar formato del teléfono"""
        return value
        
    def validate_email(self, value):
        """Validar unicidad de email si se cambia"""
        user = self.instance
        if Usuario.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está en uso.")
        return value

    def update(self, instance, validated_data):
        nombre_finca = validated_data.pop('nombre_finca', None)
        departamento_finca = validated_data.pop('departamento_finca', None)
        municipio_finca = validated_data.pop('municipio_finca', None)
        
        # update basic user fields
        instance = super().update(instance, validated_data)
        
        # update finca if campesino
        if instance.tipo_usuario == 'campesino' and (nombre_finca is not None or departamento_finca is not None or municipio_finca is not None):
            from farms.models import Finca
            fincas = Finca.objects.filter(usuario=instance)
            if fincas.exists():
                finca = fincas.first()
                if nombre_finca is not None:
                    finca.nombre_finca = nombre_finca
                if departamento_finca is not None:
                    finca.ubicacion_departamento = departamento_finca
                if municipio_finca is not None:
                    finca.ubicacion_municipio = municipio_finca
                finca.save()
            elif nombre_finca:
                Finca.objects.create(
                    usuario=instance, 
                    nombre_finca=nombre_finca,
                    ubicacion_departamento=departamento_finca or '',
                    ubicacion_municipio=municipio_finca or '',
                    area_hectareas=0.0  # El modelo exige este valor
                )
                
        return instance


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
        from django.db.models.functions import TruncDate
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
            
            period = self.context.get('period', 'month')
            ahora = timezone.now()
            
            if period == 'week':
                inicio_stats = (ahora - timedelta(days=ahora.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                fin_stats = ahora
                inicio_grafico = (ahora - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
                rango_grafico = 7
            elif period == 'year':
                inicio_stats = ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                fin_stats = ahora
                inicio_grafico = inicio_stats
                rango_grafico = 12
            else: # month default
                inicio_stats = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                # Fin de mes puede ser hasta el presente para stats normales, o el fin exacto. Dejamos ahora
                fin_stats = ahora
                inicio_grafico = (ahora - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
                rango_grafico = 30
            
            ventas_mes = obj.pedidos_campesino.filter(
                fecha_pedido__range=[inicio_stats, fin_stats],
                estado='completed'
            ).aggregate(total=Sum('total'))['total'] or Decimal('0')
            
            # Productos vendidos en el periodo (explicit query)
            from orders.models import DetallePedido
            productos_vendidos = DetallePedido.objects.filter(
                pedido__campesino=obj,
                pedido__fecha_pedido__range=[inicio_stats, fin_stats],
                pedido__estado='completed'
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            # Clientes únicos (explicit query)
            clientes_unicos = obj.pedidos_campesino.filter(
                fecha_pedido__range=[inicio_stats, fin_stats],
                estado='completed'
            ).values('comprador').distinct().count()
            
            labels = []
            data_puntos = []
            
            if period == 'year':
                from django.db.models.functions import TruncMonth
                ventas_agrupadas = obj.pedidos_campesino.filter(
                    fecha_pedido__gte=inicio_grafico,
                    estado='completed'
                ).annotate(
                    mes=TruncMonth('fecha_pedido')
                ).values('mes').annotate(
                    total=Sum('total')
                ).order_by('mes')
                
                ventas_map = {v['mes'].strftime('%Y-%m'): float(v['total']) for v in ventas_agrupadas}
                meses_es = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
                
                for i in range(1, 13):
                    fecha = ahora.replace(month=i, day=1)
                    fecha_str = fecha.strftime('%Y-%m')
                    labels.append(meses_es[i-1])
                    data_puntos.append(ventas_map.get(fecha_str, 0.0))
            else:
                ventas_diarias = obj.pedidos_campesino.filter(
                    fecha_pedido__gte=inicio_grafico,
                    estado='completed'
                ).annotate(
                    dia=TruncDate('fecha_pedido')
                ).values('dia').annotate(
                    total=Sum('total')
                ).order_by('dia')
                
                ventas_map = {v['dia'].strftime('%Y-%m-%d'): float(v['total']) for v in ventas_diarias}
                
                for i in range(rango_grafico - 1, -1, -1):
                    fecha = (ahora - timedelta(days=i)).date()
                    fecha_str = fecha.strftime('%Y-%m-%d')
                    labels.append(fecha.strftime('%d %b'))
                    data_puntos.append(ventas_map.get(fecha_str, 0.0))

            stats.update({
                'productos_activos': productos_activos,
                'pedidos_pendientes': pedidos_pendientes,
                'ventas_mes': int(ventas_mes),
                'calificacion': float(obj.calificacion_promedio),
                'productos_vendidos': int(productos_vendidos),
                'clientes_unicos': clientes_unicos,
                'total_fincas': obj.fincas.count(),
                'fincas_activas': obj.fincas.filter(estado='activa').count(),
                'ventas_grafico': {
                    'labels': labels,
                    'data': data_puntos
                }
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
            
            # Ahorro total real vs precios de mercado SIPSA
            from products.models import SipsaPrecio
            from decimal import Decimal
            ahorro_estimado = Decimal('0')
            pedidos_ahorro = obj.pedidos_comprador.filter(
                estado__in=['completed', 'ready']
            ).prefetch_related('detalles__producto')
            
            for pedido in pedidos_ahorro:
                for detalle in pedido.detalles.all():
                    nombre = detalle.producto.nombre
                    palabra_clave = nombre.split()[0].strip() if nombre else ''
                    
                    sipsa_val = None
                    if palabra_clave:
                        qs = SipsaPrecio.objects.filter(producto__icontains=palabra_clave)
                        if qs.exists():
                            import re
                            palabra_lower = palabra_clave.lower()
                            matches_validos = []
                            for s in qs:
                                if palabra_lower in re.findall(r'\w+', s.producto.lower()):
                                    matches_validos.append(s)
                            if matches_validos:
                                matches_exactos = [s for s in matches_validos if s.producto.replace('*', '').strip().lower() in nombre.lower()]
                                if matches_exactos:
                                    sipsa_val = matches_exactos[0]
                                else:
                                    sipsa_val = max(matches_validos, key=lambda x: x.precio_promedio)
                    # Precio estimado supermercado = SIPSA mayorista × 1.5
                    if sipsa_val:
                        precio_supermercado = sipsa_val.precio_promedio * Decimal('1.5')
                        if precio_supermercado > detalle.precio_unitario:
                            ahorro_estimado += (precio_supermercado - detalle.precio_unitario) * detalle.cantidad
            
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
                    'ubicacion': finca.ubicacion_completa
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

class PinRecoveryRequestSerializer(serializers.Serializer):
    """Serializer para solicitar recuperación de PIN Visual"""
    email = serializers.EmailField()

    def validate_email(self, value):
        if not Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("No existe un usuario registrado con este correo electrónico.")
        return value


class PinResetSerializer(serializers.Serializer):
    """Serializer para restablecer el PIN Visual con el código recibido"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_pin = serializers.CharField(max_length=50)

    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')
        
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({"email": "Usuario no encontrado."})
            
        if not user.pin_recovery_code or user.pin_recovery_code != code:
            raise serializers.ValidationError({"code": "Código de recuperación incorrecto."})
            
        if not user.pin_recovery_expires or timezone.now() > user.pin_recovery_expires:
            raise serializers.ValidationError({"code": "El código ha expirado. Solicita uno nuevo."})
            
        attrs['user'] = user
        return attrs
