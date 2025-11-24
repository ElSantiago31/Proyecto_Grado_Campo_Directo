from django.contrib import admin
from django.utils.html import format_html
from .models import CategoriaProducto, Producto


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    """
    Admin para categorías de productos
    """
    
    list_display = ['nombre', 'icono', 'estado', 'productos_count_display', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'icono')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
    
    def productos_count_display(self, obj):
        """Muestra el número de productos en la categoría"""
        count = obj.productos_count()
        return format_html(
            '<span title="Productos disponibles en esta categoría">{} productos</span>',
            count
        )
    
    productos_count_display.short_description = 'Productos'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """
    Admin para productos
    """
    
    list_display = [
        'nombre', 'campesino_display', 'categoria', 'precio_formateado',
        'stock_disponible', 'estado', 'calidad', 'fecha_creacion'
    ]
    
    list_filter = [
        'estado', 'calidad', 'categoria', 'unidad_medida',
        'disponible_entrega_inmediata', 'fecha_creacion', 'usuario__tipo_usuario'
    ]
    
    search_fields = [
        'nombre', 'descripcion', 'tags', 'usuario__nombre', 
        'usuario__apellido', 'finca__nombre_finca'
    ]
    
    readonly_fields = [
        'fecha_creacion', 'fecha_actualizacion', 'precio_formateado', 'is_disponible'
    ]
    
    autocomplete_fields = ['usuario', 'finca', 'categoria']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'finca', 'categoria', 'nombre', 'descripcion')
        }),
        ('Precio y Stock', {
            'fields': ('precio_por_kg', 'precio_formateado', 'stock_disponible', 'unidad_medida')
        }),
        ('Estado y Calidad', {
            'fields': ('estado', 'is_disponible', 'calidad')
        }),
        ('Imágenes', {
            'fields': ('imagen_principal',),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('tags', 'fecha_cosecha', 'fecha_vencimiento'),
            'classes': ('collapse',)
        }),
        ('Límites de Venta', {
            'fields': ('peso_minimo_venta', 'peso_maximo_venta'),
            'classes': ('collapse',)
        }),
        ('Entrega', {
            'fields': ('disponible_entrega_inmediata', 'tiempo_preparacion_dias'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def campesino_display(self, obj):
        """Muestra el campesino propietario"""
        return obj.usuario.get_full_name()
    
    campesino_display.short_description = 'Campesino'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'usuario', 'finca', 'categoria'
        )
    
    # Filtros personalizados en el sidebar
    def get_list_filter(self, request):
        filters = list(self.list_filter)
        # Añadir filtros dinámicos si es necesario
        return filters
    
    # Acciones personalizadas
    actions = ['marcar_como_disponible', 'marcar_como_agotado']
    
    def marcar_como_disponible(self, request, queryset):
        """Acción para marcar productos como disponibles"""
        updated = queryset.update(estado='disponible')
        self.message_user(
            request, 
            f'{updated} producto(s) marcado(s) como disponible(s).'
        )
    marcar_como_disponible.short_description = "Marcar seleccionados como disponibles"
    
    def marcar_como_agotado(self, request, queryset):
        """Acción para marcar productos como agotados"""
        updated = queryset.update(estado='agotado')
        self.message_user(
            request, 
            f'{updated} producto(s) marcado(s) como agotado(s).'
        )
    marcar_como_agotado.short_description = "Marcar seleccionados como agotados"
