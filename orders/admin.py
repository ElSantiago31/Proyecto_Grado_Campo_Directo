from django.contrib import admin
from django.utils.html import format_html
from .models import Pedido, DetallePedido, AuditLogPedido


class DetallePedidoInline(admin.TabularInline):
    """
    Inline para mostrar detalles de pedido
    """
    model = DetallePedido
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal']


class AuditLogInline(admin.TabularInline):
    """
    Inline para mostrar el historial de cambios de un pedido (solo lectura)
    """
    model = AuditLogPedido
    extra = 0
    can_delete = False
    readonly_fields = ['timestamp', 'usuario', 'estado_anterior', 'estado_nuevo', 'notas', 'ip_address']
    fields = ['timestamp', 'usuario', 'estado_anterior', 'estado_nuevo', 'notas']
    ordering = ['timestamp']
    verbose_name = 'Entrada de Auditoría'
    verbose_name_plural = '📜 Historial de Cambios'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """
    Admin para pedidos
    """
    
    list_display = [
        'id', 'comprador_display', 'campesino_display', 'total',
        'estado_display', 'fecha_pedido', 'metodo_pago'
    ]
    
    list_filter = [
        'estado', 'metodo_pago', 'fecha_pedido',
        'fecha_entrega_programada'
    ]
    
    search_fields = [
        'id', 'codigo_seguimiento', 'comprador__nombre', 'comprador__apellido',
        'campesino__nombre', 'campesino__apellido', 'notas_comprador', 'notas_campesino'
    ]
    
    readonly_fields = [
        'fecha_pedido', 'fecha_confirmacion', 'fecha_preparacion',
        'fecha_entrega', 'fecha_completado', 'codigo_seguimiento',
        'estado_display_color', 'puede_ser_cancelado'
    ]
    
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('id', 'codigo_seguimiento', 'comprador', 'campesino', 'total')
        }),
        ('Estado y Seguimiento', {
            'fields': ('estado', 'estado_display_color', 'puede_ser_cancelado', 'metodo_pago')
        }),
        ('Fechas', {
            'fields': (
                'fecha_pedido', 'fecha_confirmacion', 'fecha_preparacion',
                'fecha_entrega', 'fecha_completado'
            ),
            'classes': ('collapse',)
        }),
        ('Entrega', {
            'fields': (
                'direccion_entrega', 'telefono_contacto',
                'fecha_entrega_programada', 'hora_entrega_programada'
            ),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notas_comprador', 'notas_campesino'),
            'classes': ('collapse',)
        }),
        ('Calificaciones', {
            'fields': ('calificacion_comprador', 'calificacion_campesino', 'comentario_calificacion'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [DetallePedidoInline, AuditLogInline]
    
    def comprador_display(self, obj):
        """Muestra el comprador"""
        return obj.comprador.get_full_name()
    
    comprador_display.short_description = 'Comprador'
    
    def campesino_display(self, obj):
        """Muestra el campesino"""
        return obj.campesino.get_full_name()
    
    campesino_display.short_description = 'Campesino'
    
    def estado_display(self, obj):
        """Muestra el estado con colores"""
        color = obj.estado_display_color
        colors_map = {
            'warning': '#ffc107',
            'info': '#17a2b8',
            'primary': '#007bff',
            'success': '#28a745',
            'danger': '#dc3545',
            'secondary': '#6c757d'
        }
        
        color_hex = colors_map.get(color, '#6c757d')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color_hex, obj.get_estado_display()
        )
    
    estado_display.short_description = 'Estado'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'comprador', 'campesino'
        ).prefetch_related('detalles')
    
    # Acciones personalizadas
    actions = ['confirmar_pedidos', 'marcar_como_completados']
    
    def confirmar_pedidos(self, request, queryset):
        """Acción para confirmar pedidos pendientes"""
        updated = 0
        for pedido in queryset:
            if pedido.estado == 'pending':
                pedido.actualizar_estado('confirmed', usuario=request.user)
                updated += 1
        
        self.message_user(
            request, 
            f'{updated} pedido(s) confirmado(s).'
        )
    confirmar_pedidos.short_description = "Confirmar pedidos seleccionados"
    
    def marcar_como_completados(self, request, queryset):
        """Acción para marcar pedidos como completados"""
        updated = 0
        for pedido in queryset:
            if pedido.estado == 'ready':
                pedido.actualizar_estado('completed', usuario=request.user)
                updated += 1
        
        self.message_user(
            request, 
            f'{updated} pedido(s) marcado(s) como completado(s).'
        )
    marcar_como_completados.short_description = "Marcar seleccionados como completados"


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    """
    Admin para detalles de pedidos
    """
    
    list_display = [
        'pedido', 'producto_display', 'cantidad', 'precio_unitario', 'subtotal'
    ]
    
    list_filter = [
        'pedido__estado', 'producto__categoria', 'pedido__fecha_pedido'
    ]
    
    search_fields = [
        'pedido__id', 'producto__nombre', 'nombre_producto_snapshot'
    ]
    
    readonly_fields = ['subtotal']
    
    def producto_display(self, obj):
        """Muestra el producto con snapshot"""
        return f"{obj.nombre_producto_snapshot} ({obj.unidad_medida_snapshot})"
    
    producto_display.short_description = 'Producto'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'pedido', 'producto'
        )


@admin.register(AuditLogPedido)
class AuditLogPedidoAdmin(admin.ModelAdmin):
    """
    Vista de sólo lectura del log de auditoría de pedidos (RNF14).
    Estos registros son inmutables: no se pueden crear, editar ni borrar desde el admin.
    """
    list_display = ['timestamp', 'pedido', 'usuario_display', 'estado_anterior', 'flecha', 'estado_nuevo', 'notas_preview']
    list_filter = ['estado_nuevo', 'timestamp']
    search_fields = ['pedido__id', 'usuario__email', 'usuario__nombre']
    readonly_fields = ['pedido', 'usuario', 'estado_anterior', 'estado_nuevo', 'notas', 'timestamp', 'ip_address']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def usuario_display(self, obj):
        return obj.usuario.email if obj.usuario else '— Sistema —'
    usuario_display.short_description = 'Realizado por'

    def flecha(self, obj):
        return '→'
    flecha.short_description = ''

    def notas_preview(self, obj):
        if obj.notas:
            return obj.notas[:60] + ('...' if len(obj.notas) > 60 else '')
        return '—'
    notas_preview.short_description = 'Notas'
