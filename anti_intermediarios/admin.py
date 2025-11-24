"""
Administración para funcionalidades anti-intermediarios
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Conversacion, Mensaje, TransparenciaPrecios, ReporteImpacto


class MensajeInline(admin.TabularInline):
    """
    Inline para mostrar mensajes en conversaciones
    """
    model = Mensaje
    extra = 0
    readonly_fields = ['fecha_envio', 'leido']
    fields = ['remitente', 'contenido', 'tipo_mensaje', 'fecha_envio', 'leido']
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related('remitente')


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    """
    Admin para conversaciones
    """
    list_display = [
        'id', 'campesino_link', 'comprador_link', 'producto_link', 'activa',
        'total_mensajes', 'mensajes_no_leidos', 'fecha_creacion'
    ]
    list_filter = ['activa', 'fecha_creacion', 'fecha_actualizacion']
    search_fields = [
        'campesino__nombre', 'comprador__nombre', 'producto__nombre'
    ]
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'total_mensajes']
    inlines = [MensajeInline]
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('campesino', 'comprador', 'producto', 'activa')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('total_mensajes',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related(
            'campesino', 'comprador', 'producto'
        ).prefetch_related('mensajes')
    
    def campesino_link(self, obj):
        """Link al campesino"""
        if obj.campesino:
            url = reverse('admin:accounts_usuario_change', args=[obj.campesino.id])
            return format_html('<a href="{}">{}</a>', url, obj.campesino.nombre)
        return '-'
    campesino_link.short_description = 'Campesino'
    
    def comprador_link(self, obj):
        """Link al comprador"""
        if obj.comprador:
            url = reverse('admin:accounts_usuario_change', args=[obj.comprador.id])
            return format_html('<a href="{}">{}</a>', url, obj.comprador.nombre)
        return '-'
    comprador_link.short_description = 'Comprador'
    
    def producto_link(self, obj):
        """Link al producto"""
        if obj.producto:
            url = reverse('admin:products_producto_change', args=[obj.producto.id])
            return format_html('<a href="{}">{}</a>', url, obj.producto.nombre)
        return '-'
    producto_link.short_description = 'Producto'
    
    def total_mensajes(self, obj):
        """Total de mensajes en la conversación"""
        return obj.mensajes.count()
    total_mensajes.short_description = 'Total Mensajes'
    
    def mensajes_no_leidos(self, obj):
        """Mensajes no leídos"""
        no_leidos = obj.mensajes.filter(leido=False).count()
        if no_leidos > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                no_leidos
            )
        return '0'
    mensajes_no_leidos.short_description = 'No Leídos'
    
    actions = ['archivar_conversaciones', 'activar_conversaciones']
    
    def archivar_conversaciones(self, request, queryset):
        """Archivar conversaciones seleccionadas"""
        updated = queryset.update(activa=False)
        self.message_user(
            request, 
            f'{updated} conversaciones archivadas correctamente.'
        )
    archivar_conversaciones.short_description = "Archivar conversaciones seleccionadas"
    
    def activar_conversaciones(self, request, queryset):
        """Activar conversaciones seleccionadas"""
        updated = queryset.update(activa=True)
        self.message_user(
            request, 
            f'{updated} conversaciones activadas correctamente.'
        )
    activar_conversaciones.short_description = "Activar conversaciones seleccionadas"


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    """
    Admin para mensajes
    """
    list_display = [
        'id', 'conversacion_link', 'remitente_link', 'tipo_mensaje', 
        'contenido_preview', 'leido', 'fecha_envio'
    ]
    list_filter = ['tipo_mensaje', 'leido', 'fecha_envio']
    search_fields = ['contenido', 'remitente__nombre']
    readonly_fields = ['fecha_envio']
    date_hierarchy = 'fecha_envio'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('conversacion', 'remitente', 'contenido', 'tipo_mensaje')
        }),
        ('Estado', {
            'fields': ('leido', 'fecha_envio')
        })
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related(
            'conversacion', 'remitente'
        )
    
    def conversacion_link(self, obj):
        """Link a la conversación"""
        if obj.conversacion:
            url = reverse('admin:anti_intermediarios_conversacion_change', 
                         args=[obj.conversacion.id])
            return format_html('<a href="{}">Conversación #{}</a>', 
                             url, obj.conversacion.id)
        return '-'
    conversacion_link.short_description = 'Conversación'
    
    def remitente_link(self, obj):
        """Link al remitente"""
        if obj.remitente:
            url = reverse('admin:accounts_usuario_change', args=[obj.remitente.id])
            return format_html('<a href="{}">{}</a>', url, obj.remitente.nombre)
        return '-'
    remitente_link.short_description = 'Remitente'
    
    def contenido_preview(self, obj):
        """Preview del contenido del mensaje"""
        if len(obj.contenido) > 50:
            return obj.contenido[:50] + '...'
        return obj.contenido
    contenido_preview.short_description = 'Contenido'
    
    actions = ['marcar_como_leidos', 'marcar_como_no_leidos']
    
    def marcar_como_leidos(self, request, queryset):
        """Marcar mensajes como leídos"""
        updated = queryset.update(leido=True)
        self.message_user(
            request,
            f'{updated} mensajes marcados como leídos.'
        )
    marcar_como_leidos.short_description = "Marcar como leídos"
    
    def marcar_como_no_leidos(self, request, queryset):
        """Marcar mensajes como no leídos"""
        updated = queryset.update(leido=False)
        self.message_user(
            request,
            f'{updated} mensajes marcados como no leídos.'
        )
    marcar_como_no_leidos.short_description = "Marcar como no leídos"


@admin.register(TransparenciaPrecios)
class TransparenciaPreciosAdmin(admin.ModelAdmin):
    """
    Admin para transparencia de precios
    """
    list_display = [
        'id', 'producto_link', 'precio_campo_directo', 'precio_mercado_tradicional',
        'ahorro_absoluto_display', 'ahorro_porcentual_display', 'ciudad_referencia',
        'fecha_registro'
    ]
    list_filter = [
        'fuente_precio_referencia', 'ciudad_referencia', 'fecha_registro'
    ]
    search_fields = ['producto__nombre', 'ciudad_referencia']
    readonly_fields = ['ahorro_absoluto', 'ahorro_porcentual', 'fecha_registro']
    date_hierarchy = 'fecha_registro'
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('producto',)
        }),
        ('Precios', {
            'fields': ('precio_campo_directo', 'precio_mercado_tradicional')
        }),
        ('Ahorros (Calculados)', {
            'fields': ('ahorro_absoluto', 'ahorro_porcentual'),
            'classes': ('collapse',)
        }),
        ('Referencia', {
            'fields': ('fuente_precio_referencia', 'ciudad_referencia', 'notas')
        }),
        ('Fechas', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related('producto')
    
    def producto_link(self, obj):
        """Link al producto"""
        if obj.producto:
            url = reverse('admin:products_producto_change', args=[obj.producto.id])
            return format_html('<a href="{}">{}</a>', url, obj.producto.nombre)
        return '-'
    producto_link.short_description = 'Producto'
    
    def ahorro_absoluto_display(self, obj):
        """Mostrar ahorro absoluto formateado"""
        if obj.ahorro_absoluto > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">${:,.2f}</span>',
                obj.ahorro_absoluto
            )
        return f'${obj.ahorro_absoluto:,.2f}'
    ahorro_absoluto_display.short_description = 'Ahorro ($)'
    
    def ahorro_porcentual_display(self, obj):
        """Mostrar ahorro porcentual formateado"""
        if obj.ahorro_porcentual > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{:.1f}%</span>',
                obj.ahorro_porcentual
            )
        return f'{obj.ahorro_porcentual:.1f}%'
    ahorro_porcentual_display.short_description = 'Ahorro (%)'


@admin.register(ReporteImpacto)
class ReporteImpactoAdmin(admin.ModelAdmin):
    """
    Admin para reportes de impacto
    """
    list_display = [
        'id', 'fecha_inicio', 'fecha_fin', 'total_transacciones',
        'ahorro_total_display', 'campesinos_beneficiados', 'fecha_generacion'
    ]
    list_filter = ['fecha_generacion', 'fecha_inicio', 'fecha_fin']
    readonly_fields = [
        'total_transacciones', 'ahorro_total_generado', 'campesinos_beneficiados',
        'compradores_beneficiados', 'productos_top', 'fecha_generacion'
    ]
    date_hierarchy = 'fecha_generacion'
    
    fieldsets = (
        ('Período del Reporte', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Métricas Calculadas', {
            'fields': (
                'total_transacciones', 'ahorro_total_generado', 'campesinos_beneficiados',
                'compradores_beneficiados'
            ),
            'classes': ('collapse',)
        }),
        ('Productos Top', {
            'fields': ('productos_top',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_generacion',),
            'classes': ('collapse',)
        })
    )
    
    def ahorro_total_display(self, obj):
        """Mostrar ahorro total formateado"""
        if obj.ahorro_total_generado > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">${:,.2f}</span>',
                obj.ahorro_total_generado
            )
        return f'${obj.ahorro_total_generado:,.2f}'
    ahorro_total_display.short_description = 'Ahorro Total'
    
    def has_add_permission(self, request):
        """Los reportes se generan automáticamente"""
        return False
