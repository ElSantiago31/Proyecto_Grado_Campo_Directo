"""
Serializers para fincas y certificaciones
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Finca

Usuario = get_user_model()


class FincaListSerializer(serializers.ModelSerializer):
    """
    Serializer para lista de fincas (vista resumida)
    """
    campesino_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    ubicacion_completa = serializers.ReadOnlyField()
    productos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Finca
        fields = [
            'id', 'nombre_finca', 'campesino_nombre', 'ubicacion_completa',
            'area_hectareas', 'tipo_cultivo', 'estado', 'productos_count',
            'fecha_creacion'
        ]
    
    def get_productos_count(self, obj):
        return obj.productos_count()


class FincaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para una finca específica
    """
    campesino = serializers.SerializerMethodField()
    ubicacion_completa = serializers.ReadOnlyField()
    tiene_coordenadas = serializers.ReadOnlyField()
    productos_count = serializers.SerializerMethodField()
    productos_disponibles_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Finca
        fields = [
            'id', 'nombre_finca', 'ubicacion_departamento', 'ubicacion_municipio',
            'ubicacion_completa', 'direccion', 'area_hectareas', 'tipo_cultivo',
            'descripcion', 'latitud', 'longitud', 'tiene_coordenadas', 'estado',
            'fecha_creacion', 'fecha_actualizacion', 'campesino',
            'productos_count', 'productos_disponibles_count'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_campesino(self, obj):
        return {
            'id': obj.usuario.id,
            'nombre': obj.usuario.get_full_name(),
            'email': obj.usuario.email,
            'telefono': obj.usuario.telefono,
            'calificacion_promedio': obj.usuario.calificacion_promedio,
            'total_calificaciones': obj.usuario.total_calificaciones,
            'avatar': obj.usuario.avatar.url if obj.usuario.avatar else None
        }
    
    def get_productos_count(self, obj):
        return obj.productos_count()
    
    def get_productos_disponibles_count(self, obj):
        return obj.productos_disponibles_count()


class FincaCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar fincas
    """
    
    class Meta:
        model = Finca
        fields = [
            'nombre_finca', 'ubicacion_departamento', 'ubicacion_municipio',
            'direccion', 'area_hectareas', 'tipo_cultivo', 'descripcion',
            'latitud', 'longitud', 'estado'
        ]
    
    def validate_area_hectareas(self, value):
        """Validar que el área sea positiva"""
        if value <= 0:
            raise serializers.ValidationError("El área debe ser mayor a 0 hectáreas")
        return value
    
    def validate(self, attrs):
        """Validaciones adicionales"""
        latitud = attrs.get('latitud')
        longitud = attrs.get('longitud')
        
        # Si se proporciona una coordenada, ambas deben estar presentes
        if (latitud is not None) != (longitud is not None):
            raise serializers.ValidationError(
                "Debe proporcionar tanto latitud como longitud, o ninguna de las dos"
            )
        
        # Validar rangos de coordenadas para Colombia
        if latitud is not None:
            if not (-4.5 <= latitud <= 13.5):
                raise serializers.ValidationError(
                    "La latitud debe estar en el rango válido para Colombia"
                )
        
        if longitud is not None:
            if not (-82 <= longitud <= -66):
                raise serializers.ValidationError(
                    "La longitud debe estar en el rango válido para Colombia"
                )
        
        return attrs
    
    def create(self, validated_data):
        # Asignar usuario automáticamente
        validated_data['usuario'] = self.context['request'].user
        return Finca.objects.create(**validated_data)

