"""
Serializers para productos y categorías
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import CategoriaProducto, Producto, SipsaPrecio

Usuario = get_user_model()


class CategoriaProductoSerializer(serializers.ModelSerializer):
    """
    Serializer para categorías de productos
    """
    productos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CategoriaProducto
        fields = [
            'id', 'nombre', 'descripcion', 'icono', 
            'estado', 'fecha_creacion', 'productos_count'
        ]
        read_only_fields = ['id', 'fecha_creacion']
    
    def get_productos_count(self, obj):
        """Cuenta los productos disponibles en esta categoría"""
        return obj.productos_count()


class ProductoListSerializer(serializers.ModelSerializer):
    """
    Serializer para lista de productos (vista resumida)
    """
    campesino = serializers.IntegerField(source='usuario.id', read_only=True)
    campesino_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    categoria_icono = serializers.CharField(source='categoria.icono', read_only=True)
    finca_nombre = serializers.CharField(source='finca.nombre_finca', read_only=True)
    ubicacion = serializers.CharField(source='finca.ubicacion_completa', read_only=True)
    precio_formateado = serializers.ReadOnlyField()
    is_disponible = serializers.ReadOnlyField()
    tags_list = serializers.SerializerMethodField()
    campesino_calificacion = serializers.DecimalField(source='usuario.calificacion_promedio', max_digits=3, decimal_places=1, read_only=True)
    
    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'precio_por_kg', 'precio_formateado',
            'stock_disponible', 'unidad_medida', 'estado', 'is_disponible',
            'imagen_principal', 'calidad', 'fecha_cosecha', 'disponible_entrega_inmediata',
            'campesino', 'campesino_nombre', 'categoria_nombre', 'categoria_icono', 
            'finca_nombre', 'ubicacion', 'tags_list', 'campesino_calificacion'
        ]
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()


class ProductoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para un producto específico
    """
    campesino = serializers.SerializerMethodField()
    categoria = CategoriaProductoSerializer(read_only=True)
    finca = serializers.SerializerMethodField()
    precio_formateado = serializers.ReadOnlyField()
    is_disponible = serializers.ReadOnlyField()
    tags_list = serializers.SerializerMethodField()
    galeria_urls = serializers.SerializerMethodField()
    
    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'precio_por_kg', 'precio_formateado',
            'stock_disponible', 'unidad_medida', 'estado', 'is_disponible',
            'imagen_principal', 'galeria_urls', 'tags_list', 'calidad',
            'fecha_cosecha', 'fecha_vencimiento', 'peso_minimo_venta',
            'peso_maximo_venta', 'disponible_entrega_inmediata',
            'tiempo_preparacion_dias', 'fecha_creacion', 'fecha_actualizacion',
            'campesino', 'categoria', 'finca'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_campesino(self, obj):
        return {
            'id': obj.usuario.id,
            'nombre': obj.usuario.get_full_name(),
            'email': obj.usuario.email,
            'calificacion_promedio': obj.usuario.calificacion_promedio,
            'total_calificaciones': obj.usuario.total_calificaciones,
            'avatar': obj.usuario.avatar.url if obj.usuario.avatar else None
        }
    
    def get_finca(self, obj):
        return {
            'id': obj.finca.id,
            'nombre': obj.finca.nombre_finca,
            'ubicacion': obj.finca.ubicacion_completa,
            'area_hectareas': obj.finca.area_hectareas,
            'tipo_cultivo': obj.finca.get_tipo_cultivo_display(),
            'certificaciones_count': obj.finca.certificaciones.filter(estado='vigente').count() if hasattr(obj.finca, 'certificaciones') else 0
        }
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()
    
    def get_galeria_urls(self, obj):
        return obj.get_galeria_urls()


class ProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar productos
    """
    tags_list = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        help_text="Lista de tags para el producto"
    )
    
    class Meta:
        model = Producto
        fields = [
            'categoria', 'finca', 'nombre', 'descripcion', 'precio_por_kg',
            'stock_disponible', 'unidad_medida', 'estado', 'imagen_principal',
            'tags_list', 'calidad', 'fecha_cosecha', 'fecha_vencimiento',
            'peso_minimo_venta', 'peso_maximo_venta', 'disponible_entrega_inmediata',
            'tiempo_preparacion_dias'
        ]
    
    def validate_finca(self, value):
        """Validar que la finca pertenece al usuario autenticado"""
        user = self.context['request'].user
        if not user.is_campesino:
            raise serializers.ValidationError("Solo los campesinos pueden crear productos")
        
        if value.usuario != user:
            raise serializers.ValidationError("La finca debe pertenecerte")
        
        return value
    
    def validate(self, attrs):
        """Validaciones adicionales"""
        peso_min = attrs.get('peso_minimo_venta', 0.5)
        peso_max = attrs.get('peso_maximo_venta', 100.0)
        
        if peso_min >= peso_max:
            raise serializers.ValidationError(
                "El peso mínimo debe ser menor que el peso máximo"
            )
            
        precio = attrs.get('precio_por_kg')
        nombre = attrs.get('nombre')
        finca = attrs.get('finca')
        unidad = attrs.get('unidad_medida', 'kg')
        
        # Validar límite SIPSA solo para medidas de peso exacto
        unidades_peso = ['kg', 'libra', 'arroba', 'gramo']
        
        if precio and nombre and unidad in unidades_peso:
            # Extraemos la primera palabra (ej 'Papa')
            palabra_clave = nombre.split()[0].strip() if nombre else ''
            sipsa_qs = SipsaPrecio.objects.none()
            if palabra_clave:
                sipsa_qs = SipsaPrecio.objects.filter(producto__icontains=palabra_clave)
            
            sipsa_val = None
            if sipsa_qs.exists():
                import re
                palabra_lower = palabra_clave.lower()
                opciones = []
                if finca and finca.ubicacion_municipio:
                    opciones.append(sipsa_qs.filter(ciudad__icontains=finca.ubicacion_municipio))
                opciones.append(sipsa_qs)
                
                matches_validos = []
                for qs in opciones:
                    for s in qs:
                        palabras_sipsa = re.findall(r'\w+', s.producto.lower())
                        if palabra_lower in palabras_sipsa:
                            matches_validos.append(s)
                    if matches_validos:
                        break # Si hay matches locales, priorizarlos
                
                if matches_validos:
                    # Intento 1: Coincidencia exacta de variante (Papa sabanera in "Papa sabanera sucia")
                    matches_exactos = [s for s in matches_validos if s.producto.replace('*', '').strip().lower() in nombre.lower()]
                    es_exacto = False
                    if matches_exactos:
                        sipsa_val = matches_exactos[0]
                        es_exacto = True
                    else:
                        # Intento 2: Beneficio campesino (Tomar el techo más alto de la variante 'Papa')
                        sipsa_val = max(matches_validos, key=lambda x: x.precio_promedio)
                
            if sipsa_val:
                # Calcular el precio equivalente por kilogramo ingresado por el usuario
                precio_equivalente_kg = precio
                if unidad == 'libra':
                    precio_equivalente_kg = precio * Decimal('2')
                elif unidad == 'arroba':
                    precio_equivalente_kg = precio / Decimal('12.5')
                elif unidad == 'gramo':
                    precio_equivalente_kg = precio * Decimal('1000')

                # El precio máximo permitido será un 130% (x1.3) del valor SIPSA (por kg)
                limite_maximo = sipsa_val.precio_promedio * Decimal('1.30')
                if precio_equivalente_kg > limite_maximo:
                    if es_exacto or sipsa_val.producto.lower() == palabra_clave.lower():
                        mensaje = (
                            f'Precio demasiado alto. Referencia DANE para "{sipsa_val.producto}": '
                            f'${sipsa_val.precio_promedio:,.0f} COP/Kg. '
                            f'Límite máximo permitido: ${limite_maximo:,.0f} COP/Kg. '
                            f'Tu precio equivale a ${precio_equivalente_kg:,.0f} COP/Kg y supera el límite.'
                        )
                    else:
                        mensaje = (
                            f'Tu variante no figura en el DANE, se usó la referencia más alta de "{sipsa_val.producto}" '
                            f'(${sipsa_val.precio_promedio:,.0f} COP/Kg). '
                            f'Límite permitido: ${limite_maximo:,.0f} COP/Kg. Tu equivalente es ${precio_equivalente_kg:,.0f} COP/Kg.'
                        )

                    raise serializers.ValidationError({
                        'precio_por_kg': mensaje
                    })
        
        return attrs
    
    def create(self, validated_data):
        tags_list = validated_data.pop('tags_list', [])
        
        # Asignar usuario automáticamente
        validated_data['usuario'] = self.context['request'].user
        
        producto = Producto.objects.create(**validated_data)
        
        # Procesar tags
        if tags_list:
            producto.set_tags_from_list(tags_list)
            producto.save()
        
        return producto
    
    def update(self, instance, validated_data):
        tags_list = validated_data.pop('tags_list', None)
        
        # Actualizar campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Procesar tags si se proporcionaron
        if tags_list is not None:
            instance.set_tags_from_list(tags_list)
        
        instance.save()
        return instance


class ProductoStockUpdateSerializer(serializers.Serializer):
    """
    Serializer para actualizar stock de productos
    """
    cantidad = serializers.IntegerField(min_value=0)
    accion = serializers.ChoiceField(choices=['set', 'add', 'subtract'])
    
    def validate(self, attrs):
        producto = self.context['producto']
        cantidad = attrs['cantidad']
        accion = attrs['accion']
        
        if accion == 'subtract' and cantidad > producto.stock_disponible:
            raise serializers.ValidationError(
                f"No se puede restar más stock del disponible ({producto.stock_disponible})"
            )
        
        return attrs