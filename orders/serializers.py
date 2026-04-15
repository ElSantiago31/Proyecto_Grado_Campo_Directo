"""
Serializers para pedidos y detalles de pedidos
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Pedido, DetallePedido
from products.models import Producto
from users.serializers import UsuarioSerializer

Usuario = get_user_model()


class DetallePedidoSerializer(serializers.ModelSerializer):
    """
    Serializer para detalles de pedidos
    """
    subtotal = serializers.ReadOnlyField()
    producto_nombre = serializers.CharField(source='nombre_producto_snapshot', read_only=True)
    
    class Meta:
        model = DetallePedido
        fields = [
            'id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario',
            'subtotal', 'nombre_producto_snapshot', 'unidad_medida_snapshot'
        ]
        read_only_fields = ['id', 'nombre_producto_snapshot', 'unidad_medida_snapshot']


class DetallePedidoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear detalles de pedidos
    """
    
    class Meta:
        model = DetallePedido
        # SEGURIDAD: precio_unitario NO se acepta del cliente.
        # Se calcula siempre desde la base de datos en validate().
        fields = ['producto', 'cantidad']
    
    def validate(self, attrs):
        """Validaciones para el detalle del pedido"""
        producto = attrs['producto']
        cantidad = attrs['cantidad']

        # SEGURIDAD: El precio SIEMPRE se toma de la base de datos.
        # NUNCA se acepta el precio enviado por el cliente para evitar
        # ataques de price manipulation.
        attrs['precio_unitario'] = producto.precio_por_kg

        # Verificar disponibilidad del producto
        disponible, mensaje = producto.puede_ser_comprado_por_cantidad(cantidad)
        if not disponible:
            raise serializers.ValidationError(f"Producto {producto.nombre}: {mensaje}")

        return attrs


class PedidoListSerializer(serializers.ModelSerializer):
    """
    Serializer para lista de pedidos (vista resumida)
    """
    comprador_nombre = serializers.CharField(source='comprador.get_full_name', read_only=True)
    campesino_nombre = serializers.CharField(source='campesino.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    estado_color = serializers.ReadOnlyField(source='estado_display_color')
    total_items = serializers.SerializerMethodField()
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'comprador_nombre', 'campesino_nombre', 'total',
            'estado', 'estado_display', 'estado_color', 'fecha_pedido',
            'fecha_entrega_programada', 'total_items', 'codigo_seguimiento', 'detalles',
            'direccion_entrega', 'telefono_contacto', 'calificacion_comprador',
            'calificacion_campesino'
        ]
    
    def get_total_items(self, obj):
        return obj.detalles.count()


class PedidoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para un pedido específico
    """
    comprador = UsuarioSerializer(read_only=True)
    campesino = UsuarioSerializer(read_only=True)
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    estado_color = serializers.ReadOnlyField(source='estado_display_color')
    puede_ser_cancelado = serializers.ReadOnlyField()
    puede_ser_calificado_por_comprador = serializers.ReadOnlyField()
    puede_ser_calificado_por_campesino = serializers.ReadOnlyField()
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'comprador', 'campesino', 'total', 'estado', 'estado_display',
            'estado_color', 'metodo_pago', 'notas_comprador', 'notas_campesino',
            'fecha_pedido', 'fecha_confirmacion', 'fecha_preparacion', 
            'fecha_entrega', 'fecha_completado', 'direccion_entrega',
            'telefono_contacto', 'fecha_entrega_programada', 'hora_entrega_programada',
            'codigo_seguimiento', 'calificacion_comprador', 'calificacion_campesino',
            'comentario_calificacion', 'detalles', 'puede_ser_cancelado',
            'puede_ser_calificado_por_comprador', 'puede_ser_calificado_por_campesino'
        ]
        read_only_fields = [
            'id', 'fecha_pedido', 'fecha_confirmacion', 'fecha_preparacion',
            'fecha_entrega', 'fecha_completado', 'codigo_seguimiento'
        ]


class PedidoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear pedidos
    """
    detalles = DetallePedidoCreateSerializer(many=True)
    
    class Meta:
        model = Pedido
        fields = [
            'campesino', 'metodo_pago', 'notas_comprador', 'direccion_entrega',
            'telefono_contacto', 'fecha_entrega_programada', 'hora_entrega_programada',
            'detalles'
        ]
    
    def validate_campesino(self, value):
        """Validar que el campesino existe y está activo"""
        if not value.is_campesino:
            raise serializers.ValidationError("El usuario especificado no es un campesino")
        
        if not value.is_activo:
            raise serializers.ValidationError("El campesino no está activo")
        
        return value
    
    def validate_detalles(self, value):
        """Validar que hay al menos un detalle"""
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un producto en el pedido")
        
        # Validar que todos los productos son del mismo campesino
        campesino_id = None
        for detalle in value:
            producto = detalle['producto']
            if campesino_id is None:
                campesino_id = producto.usuario.id
            elif producto.usuario.id != campesino_id:
                raise serializers.ValidationError(
                    "Todos los productos deben ser del mismo campesino"
                )
        
        return value
    
    def validate(self, attrs):
        """Validaciones adicionales"""
        # Verificar que el campesino coincide con los productos
        campesino = attrs['campesino']
        detalles = attrs['detalles']
        
        for detalle in detalles:
            if detalle['producto'].usuario != campesino:
                raise serializers.ValidationError(
                    f"El producto {detalle['producto'].nombre} no pertenece al campesino seleccionado"
                )
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Crear pedido con detalles"""
        detalles_data = validated_data.pop('detalles')
        
        # Asignar comprador automáticamente
        validated_data['comprador'] = self.context['request'].user
        
        # Crear pedido sin total (se calculará después)
        validated_data['total'] = 0
        pedido = Pedido.objects.create(**validated_data)
        
        # Crear detalles y calcular total
        total = 0
        for detalle_data in detalles_data:
            producto = detalle_data['producto']
            cantidad = detalle_data['cantidad']
            # SEGURIDAD: precio siempre tomado de la BD, no del cliente
            precio_unitario = producto.precio_por_kg

            # Crear detalle
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                nombre_producto_snapshot=producto.nombre,
                unidad_medida_snapshot=producto.unidad_medida
            )

            # Reducir stock
            producto.reducir_stock(cantidad)

            total += cantidad * precio_unitario
        
        # Actualizar total del pedido
        pedido.total = total
        pedido.save()
        
        # --- CÓDIGO NUEVO ESTILO OPTIMIZADO: CREAR CONVERSACION AL PROCESAR ORDEN ---
        try:
            from anti_intermediarios.models import Conversacion, Mensaje
            
            # Buscar si ya existe una conversación base entre los dos usuarios
            conversacion = Conversacion.objects.filter(
                campesino=pedido.campesino,
                comprador=pedido.comprador,
                producto__isnull=True
            ).first()
            
            if not conversacion:
                conversacion = Conversacion.objects.create(
                    campesino=pedido.campesino,
                    comprador=pedido.comprador,
                    producto=None
                )
            
            # Formatear el mensaje autogenerado por el sistema, usando como remitente al comprador
            mensaje_texto = f"📦 ¡Hola! He realizado el pedido {pedido.id} por un total de ${pedido.total:,.0f} COP.\n\n"
            if pedido.direccion_entrega:
                mensaje_texto += f"🏠 Dirección de envío: {pedido.direccion_entrega}\n"
            if pedido.telefono_contacto:
                mensaje_texto += f"📞 Teléfono: {pedido.telefono_contacto}\n"
            mensaje_texto += "\n¡Quedo atento/a a la confirmación!"
                
            Mensaje.objects.create(
                conversacion=conversacion,
                remitente=pedido.comprador,
                tipo_mensaje='texto',  # Usamos texto en lugar de sistema temporalmente para simplificar la GUI
                contenido=mensaje_texto
            )
            
            # Actualizamos el update time de la conversacion para que suba en el listado
            conversacion.save()
        except Exception as e:
            import logging
            logging.error(f"Error instanciando el chat de la orden: {str(e)}")
        
        return pedido


class PedidoUpdateEstadoSerializer(serializers.Serializer):
    """
    Serializer para actualizar estado de pedidos
    """
    nuevo_estado = serializers.ChoiceField(choices=Pedido.ESTADO_CHOICES)
    notas = serializers.CharField(required=False, allow_blank=True)
    
    def validate_nuevo_estado(self, value):
        """Validar transiciones de estado"""
        pedido = self.context['pedido']
        estado_actual = pedido.estado
        
        # Definir transiciones válidas
        transiciones_validas = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['preparing', 'cancelled'],
            'preparing': ['ready'],
            'ready': ['completed'],
            'completed': [],  # Estado final
            'cancelled': []   # Estado final
        }
        
        if value not in transiciones_validas.get(estado_actual, []):
            raise serializers.ValidationError(
                f"No se puede cambiar de estado '{estado_actual}' a '{value}'"
            )
        
        return value


class CalificacionSerializer(serializers.Serializer):
    """
    Serializer para calificar pedidos
    """
    calificacion = serializers.IntegerField(min_value=1, max_value=5)
    comentario = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate(self, attrs):
        """Validaciones para calificación"""
        pedido = self.context['pedido']
        user = self.context['user']
        
        if pedido.estado != 'completed':
            raise serializers.ValidationError("Solo se pueden calificar pedidos completados")
        
        # Verificar que el usuario puede calificar
        if user == pedido.comprador:
            if pedido.calificacion_comprador:
                raise serializers.ValidationError("Ya has calificado este pedido")
        elif user == pedido.campesino:
            if pedido.calificacion_campesino:
                raise serializers.ValidationError("Ya has calificado este pedido")
        else:
            raise serializers.ValidationError("No tienes permisos para calificar este pedido")
        
        return attrs