from django.contrib import admin
from django.utils.html import format_html
from .models import Finca


@admin.register(Finca)
class FincaAdmin(admin.ModelAdmin):
    """
    Admin para el modelo Finca
    """
    
    list_display = [
        'nombre_finca', 'usuario_display', 'ubicacion_completa', 
        'area_hectareas', 'tipo_cultivo', 'estado', 'productos_count_display'
    ]
    
    list_filter = [
        'estado', 'tipo_cultivo', 'ubicacion_departamento', 
        'fecha_creacion'
    ]
    
    search_fields = [
        'nombre_finca', 'usuario__nombre', 'usuario__apellido',
        'ubicacion_departamento', 'ubicacion_municipio'
    ]
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'nombre_finca', 'descripcion')
        }),
        ('Ubicación', {
            'fields': ('ubicacion_departamento', 'ubicacion_municipio', 'direccion')
        }),
        ('Coordenadas GPS', {
            'fields': ('latitud', 'longitud'),
            'classes': ('collapse',)
        }),
        ('Características', {
            'fields': ('area_hectareas', 'tipo_cultivo', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def usuario_display(self, obj):
        """Muestra el usuario propietario"""
        return obj.usuario.get_full_name()
    
    usuario_display.short_description = 'Campesino'
    
    def productos_count_display(self, obj):
        """Muestra el número de productos"""
        count = obj.productos_count()
        disponibles = obj.productos_disponibles_count()
        return format_html(
            '<span title="{} disponibles de {} total">{} productos</span>',
            disponibles, count, count
        )
    
    productos_count_display.short_description = 'Productos'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario')

