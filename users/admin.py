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
    
    actions = ['suspender_usuarios', 'activar_usuarios']
    
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
    def suspender_usuarios(self, request, queryset):
        """Suspende a los usuarios seleccionados"""
        # Al actualizar el estado, nuestro método save() se encargará de poner is_active=False
        for usuario in queryset:
            usuario.estado = 'suspendido'
            usuario.save()
        
        self.message_user(request, f"{queryset.count()} usuarios han sido suspendidos correctamente.")
    
    suspender_usuarios.short_description = "🚫 Suspender usuarios seleccionados"

    def activar_usuarios(self, request, queryset):
        """Activa a los usuarios seleccionados"""
        for usuario in queryset:
            usuario.estado = 'activo'
            usuario.save()
        
        self.message_user(request, f"{queryset.count()} usuarios han sido activados correctamente.")
    
    activar_usuarios.short_description = "✅ Activar/Reactivar usuarios seleccionados"
