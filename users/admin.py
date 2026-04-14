from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Admin personalizado para el modelo Usuario
    """
    
    list_display = [
        'email', 'nombre', 'apellido', 'tipo_usuario', 
        'estado', 'fecha_registro', 'calificacion_promedio_display'
    ]
    
    list_filter = [
        'tipo_usuario', 'estado', 'is_staff', 'is_active',
        'fecha_registro', 'date_joined'
    ]
    
    search_fields = ['email', 'nombre', 'apellido', 'telefono']
    
    actions = [
        'suspender_3_dias', 'suspender_7_dias', 
        'suspender_15_dias', 'suspender_30_dias', 
        'suspender_permanente', 'activar_usuarios'
    ]
    
    readonly_fields = ['fecha_registro', 'fecha_actualizacion', 'last_login']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('email', 'nombre', 'apellido', 'telefono', 'fecha_nacimiento')
        }),
        ('Tipo de Usuario', {
            'fields': ('tipo_usuario', 'estado')
        }),
        ('Avatar', {
            'fields': ('avatar',)
        }),
        ('Calificaciones', {
            'fields': ('calificacion_promedio', 'total_calificaciones'),
            'classes': ('collapse',)
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': ('fecha_registro', 'fecha_actualizacion', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Información Básica', {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'apellido', 'telefono', 'fecha_nacimiento', 'tipo_usuario', 'password1', 'password2'),
        }),
    )
    
    ordering = ['-fecha_registro']
    
    def calificacion_promedio_display(self, obj):
        """Muestra la calificación promedio con estrellas"""
        if obj.total_calificaciones > 0:
            estrellas = '⭐' * int(obj.calificacion_promedio)
            # Formateamos el número a string antes de pasarlo a format_html
            # porque en Django 5.x format_html escapa los argumentos primero, 
            # convirtiéndolos en SafeStrings que no aceptan el código de formato :.1f
            promedio_fmt = f"{obj.calificacion_promedio:.1f}"
            return format_html(
                '{} <small>({} - {} calificaciones)</small>',
                estrellas,
                promedio_fmt,
                obj.total_calificaciones
            )
        return format_html('<span style="color: #999;">Sin calificaciones</span>')
    
    calificacion_promedio_display.short_description = 'Calificación'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related()

    # Acciones masivas
    def _suspender_por_tiempo(self, request, queryset, dias=None):
        """Método auxiliar para aplicar suspensiones por tiempo"""
        from django.utils import timezone
        from datetime import timedelta
        
        hasta = timezone.now() + timedelta(days=dias) if dias else None
        
        for usuario in queryset:
            usuario.estado = 'suspendido'
            usuario.suspendido_hasta = hasta
            usuario.save()
            
        duracion = f"{dias} días" if dias else "de forma permanente"
        self.message_user(request, f"{queryset.count()} usuarios han sido suspendidos por {duracion}.")

    def suspender_3_dias(self, request, queryset):
        self._suspender_por_tiempo(request, queryset, 3)
    suspender_3_dias.short_description = "🕒 Suspender por 3 días"

    def suspender_7_dias(self, request, queryset):
        self._suspender_por_tiempo(request, queryset, 7)
    suspender_7_dias.short_description = "🗓️ Suspender por 7 días"

    def suspender_15_dias(self, request, queryset):
        self._suspender_por_tiempo(request, queryset, 15)
    suspender_15_dias.short_description = "📅 Suspender por 15 días"

    def suspender_30_dias(self, request, queryset):
        self._suspender_por_tiempo(request, queryset, 30)
    suspender_30_dias.short_description = "⚖️ Suspender por 30 días"

    def suspender_permanente(self, request, queryset):
        self._suspender_por_tiempo(request, queryset, None)
    suspender_permanente.short_description = "⛓️ Suspender Permanentemente"

    def activar_usuarios(self, request, queryset):
        """Activa a los usuarios seleccionados"""
        for usuario in queryset:
            usuario.estado = 'activo'
            usuario.suspendido_hasta = None
            usuario.save()
        
        self.message_user(request, f"{queryset.count()} usuarios han sido activados correctamente.")
    
    activar_usuarios.short_description = "✅ Activar/Reactivar usuarios seleccionados"
