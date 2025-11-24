"""
Serializers para funcionalidades anti-intermediarios
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversacion, Mensaje, TransparenciaPrecios, ReporteImpacto
from users.serializers import UsuarioSerializer

Usuario = get_user_model()


class MensajeSerializer(serializers.ModelSerializer):
    """
    Serializer para mensajes
    """
    remitente_nombre = serializers.CharField(source='remitente.get_full_name', read_only=True)
    es_oferta = serializers.ReadOnlyField()
    
    class Meta:
        model = Mensaje
        fields = [
            'id', 'conversacion', 'remitente', 'remitente_nombre', 'tipo_mensaje',
            'contenido', 'precio_ofertado', 'cantidad_ofertada', 'fecha_envio',
            'leido', 'es_oferta'
        ]
        read_only_fields = ['id', 'fecha_envio', 'remitente']


class MensajeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear mensajes
    """
    
    class Meta:
        model = Mensaje
        fields = [
            'conversacion', 'tipo_mensaje', 'contenido', 
            'precio_ofertado', 'cantidad_ofertada'
        ]
    
    def validate(self, attrs):
        """Validaciones para mensajes"""
        tipo_mensaje = attrs.get('tipo_mensaje')
        precio_ofertado = attrs.get('precio_ofertado')
        cantidad_ofertada = attrs.get('cantidad_ofertada')
        
        # Si es una oferta, debe incluir precio y cantidad
        if tipo_mensaje in ['oferta', 'negociacion']:
            if not precio_ofertado:
                raise serializers.ValidationError("Las ofertas deben incluir un precio")
            if not cantidad_ofertada:
                raise serializers.ValidationError("Las ofertas deben incluir una cantidad")
        
        return attrs
    
    def create(self, validated_data):
        # Asignar remitente automáticamente
        validated_data['remitente'] = self.context['request'].user
        return Mensaje.objects.create(**validated_data)


class ConversacionListSerializer(serializers.ModelSerializer):
    """
    Serializer para lista de conversaciones
    """
    campesino_nombre = serializers.CharField(source='campesino.get_full_name', read_only=True)
    comprador_nombre = serializers.CharField(source='comprador.get_full_name', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    ultimo_mensaje = serializers.SerializerMethodField()
    mensajes_no_leidos = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversacion
        fields = [
            'id', 'campesino', 'campesino_nombre', 'comprador', 'comprador_nombre',
            'producto', 'producto_nombre', 'fecha_creacion', 'fecha_actualizacion',
            'activa', 'ultimo_mensaje', 'mensajes_no_leidos'
        ]
    
    def get_ultimo_mensaje(self, obj):
        mensaje = obj.ultimo_mensaje()
        if mensaje:
            return {
                'contenido': mensaje.contenido[:100] + '...' if len(mensaje.contenido) > 100 else mensaje.contenido,
                'fecha_envio': mensaje.fecha_envio,
                'remitente': mensaje.remitente.get_full_name()
            }
        return None
    
    def get_mensajes_no_leidos(self, obj):
        user = self.context['request'].user
        return obj.mensajes_no_leidos_por_usuario(user)


class ConversacionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para conversaciones
    """
    campesino = UsuarioSerializer(read_only=True)
    comprador = UsuarioSerializer(read_only=True)
    producto = serializers.SerializerMethodField()
    mensajes = MensajeSerializer(many=True, read_only=True)
    mensajes_no_leidos = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversacion
        fields = [
            'id', 'campesino', 'comprador', 'producto', 'fecha_creacion',
            'fecha_actualizacion', 'activa', 'mensajes', 'mensajes_no_leidos'
        ]
    
    def get_producto(self, obj):
        if obj.producto:
            return {
                'id': obj.producto.id,
                'nombre': obj.producto.nombre,
                'precio_por_kg': obj.producto.precio_por_kg,
                'imagen_principal': obj.producto.imagen_principal.url if obj.producto.imagen_principal else None
            }
        return None
    
    def get_mensajes_no_leidos(self, obj):
        user = self.context['request'].user
        return obj.mensajes_no_leidos_por_usuario(user)


class ConversacionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear conversaciones
    """
    
    class Meta:
        model = Conversacion
        fields = ['campesino', 'producto']
    
    def validate_campesino(self, value):
        """Validar que el usuario es campesino"""
        if not value.is_campesino:
            raise serializers.ValidationError("Debe seleccionar un campesino válido")
        return value
    
    def validate_producto(self, value):
        """Validar que el producto pertenece al campesino (si se especifica)"""
        if value and hasattr(self.initial_data, 'campesino'):
            campesino = self.initial_data['campesino']
            if value.usuario != campesino:
                raise serializers.ValidationError("El producto debe pertenecer al campesino seleccionado")
        return value
    
    def create(self, validated_data):
        # Asignar comprador automáticamente
        validated_data['comprador'] = self.context['request'].user
        return Conversacion.objects.create(**validated_data)


class TransparenciaPreciosSerializer(serializers.ModelSerializer):
    """
    Serializer para transparencia de precios
    """
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    ahorro_absoluto = serializers.ReadOnlyField()
    ahorro_porcentual = serializers.ReadOnlyField()
    hay_ahorro = serializers.ReadOnlyField()
    
    class Meta:
        model = TransparenciaPrecios
        fields = [
            'id', 'producto', 'producto_nombre', 'precio_campo_directo',
            'precio_mercado_tradicional', 'fuente_precio_referencia',
            'fecha_registro', 'ciudad_referencia', 'ahorro_absoluto',
            'ahorro_porcentual', 'hay_ahorro'
        ]
        read_only_fields = ['id', 'fecha_registro']


class TransparenciaPreciosCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear registros de transparencia de precios
    """
    
    class Meta:
        model = TransparenciaPrecios
        fields = [
            'producto', 'precio_campo_directo', 'precio_mercado_tradicional',
            'fuente_precio_referencia', 'ciudad_referencia'
        ]
    
    def validate(self, attrs):
        """Validaciones para precios"""
        precio_campo = attrs['precio_campo_directo']
        precio_mercado = attrs['precio_mercado_tradicional']
        
        if precio_campo <= 0 or precio_mercado <= 0:
            raise serializers.ValidationError("Los precios deben ser mayores a cero")
        
        return attrs


class CalculadoraAhorrosSerializer(serializers.Serializer):
    """
    Serializer para calculadora de ahorros
    """
    producto_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)
    
    def validate_producto_id(self, value):
        """Validar que el producto existe"""
        from products.models import Producto
        try:
            Producto.objects.get(id=value)
            return value
        except Producto.DoesNotExist:
            raise serializers.ValidationError("Producto no encontrado")


class ReporteImpactoSerializer(serializers.ModelSerializer):
    """
    Serializer para reportes de impacto
    """
    
    class Meta:
        model = ReporteImpacto
        fields = [
            'id', 'fecha_inicio', 'fecha_fin', 'total_transacciones',
            'ahorro_total_generado', 'campesinos_beneficiados',
            'compradores_beneficiados', 'productos_top', 'fecha_generacion'
        ]
        read_only_fields = ['id', 'fecha_generacion']


class EstadisticasAntiIntermediariosSerializer(serializers.Serializer):
    """
    Serializer para estadísticas del sistema anti-intermediarios
    """
    conversaciones_activas = serializers.IntegerField()
    mensajes_totales = serializers.IntegerField()
    ahorro_promedio = serializers.DecimalField(max_digits=10, decimal_places=2)
    productos_con_comparacion = serializers.IntegerField()
    
    # Estadísticas por usuario
    mis_conversaciones = serializers.IntegerField()
    mensajes_enviados = serializers.IntegerField()
    mensajes_no_leidos = serializers.IntegerField()