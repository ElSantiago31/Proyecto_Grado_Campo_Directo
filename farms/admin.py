from django.contrib import admin
from django.utils.html import format_html
from .models import Finca, Certificacion


class CertificacionInline(admin.TabularInline):
    """
    Inline para mostrar certificaciones en la finca
    """
    model = Certificacion
    extra = 0
    readonly_fields = ['fecha_creacion']


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
    
    inlines = [CertificacionInline]
    
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


@admin.register(Certificacion)
class CertificacionAdmin(admin.ModelAdmin):
    """
    Admin para el modelo Certificación
    """
    
    list_display = [
        'nombre', 'finca_display', 'entidad_certificadora',
        'fecha_obtencion', 'fecha_vencimiento', 'estado_display'
    ]
    
    list_filter = [
        'estado', 'entidad_certificadora', 'fecha_obtencion',
        'fecha_vencimiento'
    ]
    
    search_fields = [
        'nombre', 'finca__nombre_finca', 'entidad_certificadora'
    ]
    
    readonly_fields = ['fecha_creacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('finca', 'nombre', 'descripcion')
        }),
        ('Certificación', {
            'fields': ('entidad_certificadora', 'fecha_obtencion', 'fecha_vencimiento', 'estado')
        }),
        ('Archivo', {
            'fields': ('archivo_certificado',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
    
    def finca_display(self, obj):
        """Muestra la finca y el campesino"""
        return f"{obj.finca.nombre_finca} - {obj.finca.usuario.get_full_name()}"
    
    finca_display.short_description = 'Finca'
    
    def estado_display(self, obj):
        """Muestra el estado con colores"""
        colors = {
            'vigente': '#28a745',
            'vencida': '#dc3545',
            'en_proceso': '#ffc107'
        }
        color = colors.get(obj.estado, '#6c757d')
        
        extra_info = ""
        if obj.fecha_vencimiento and obj.is_vigente:
            dias = obj.dias_para_vencer
            if dias <= 30:
                extra_info = f" (vence en {dias} días)"
        
        return format_html(
            '<span style="color: {};">{}{}</span>',
            color, obj.get_estado_display(), extra_info
        )
    
    estado_display.short_description = 'Estado'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('finca__usuario')
