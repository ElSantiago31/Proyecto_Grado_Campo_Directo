"""
Vistas del frontend para Campo Directo
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.contrib.auth import logout
from datetime import datetime, timedelta
from decimal import Decimal
import re

# Modelos locales
from products.models import Producto, SipsaPrecio
from orders.models import Pedido
from farms.models import Finca

def home(request):
    """
    Página principal de Campo Directo
    """
    context = {
        'page_title': 'Campo Directo - Conectando productores y consumidores'
    }
    return render(request, 'index.html', context)

def legal_view(request):
    """Vista para la página de marco legal y privacidad colombiana."""
    return render(request, 'legal.html')


@ensure_csrf_cookie
def login_page(request):
    """
    Página de inicio de sesión
    """
    context = {
        'page_title': 'Iniciar Sesión - Campo Directo'
    }
    return render(request, 'login.html', context)


@ensure_csrf_cookie
def register_page(request):
    """
    Página de registro
    """
    context = {
        'page_title': 'Registrarse - Campo Directo'
    }
    return render(request, 'registro.html', context)


@login_required
def dashboard(request):
    """
    Dashboard del campesino - Solo usuarios autenticados
    """
    # Verificar que el usuario sea campesino
    if not request.user.is_campesino:
        return redirect('frontend:dashboard-comprador')
    
    # Renderizar dashboard con datos reales del usuario autenticado
    return render_dashboard_with_data(request)


def render_dashboard_with_data(request):
    """
    Renderiza el dashboard con datos reales del usuario autenticado
    """
    # Obtener datos del campesino
    usuario = request.user
    
    # Estadísticas de productos
    productos_activos = usuario.productos.filter(estado='disponible').count()
    
    # Pedidos pendientes
    pedidos_pendientes = usuario.pedidos_campesino.filter(
        estado__in=['pending', 'confirmed', 'preparing']
    ).count()
    
    # Ventas del mes actual
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    ventas_mes = usuario.pedidos_campesino.filter(
        fecha_pedido__range=[inicio_mes, fin_mes],
        estado='completed'
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Calificación promedio
    calificacion = float(usuario.calificacion_promedio)
    
    # Información de la finca principal
    finca_principal = usuario.get_finca_principal()
    finca_info = None
    if finca_principal:
        finca_info = {
            'nombre': finca_principal.nombre_finca,
            'ubicacion': finca_principal.ubicacion_completa,
            'area': finca_principal.area_hectareas,
            'tipo_cultivo': finca_principal.get_tipo_cultivo_display()
        }
    
    # Actividad reciente (últimos 5 pedidos)
    actividad_reciente = []
    pedidos_recientes = usuario.pedidos_campesino.order_by('-fecha_pedido')[:5]
    for pedido in pedidos_recientes:
        tiempo_transcurrido = timezone.now() - pedido.fecha_pedido
        if tiempo_transcurrido.days == 0:
            if tiempo_transcurrido.seconds < 3600:
                tiempo = f"Hace {tiempo_transcurrido.seconds // 60} minutos"
            else:
                tiempo = f"Hace {tiempo_transcurrido.seconds // 3600} horas"
        else:
            tiempo = f"Hace {tiempo_transcurrido.days} días"
            
        actividad_reciente.append({
            'tipo': 'pedido',
            'descripcion': f"Pedido {pedido.get_estado_display().lower()} - {pedido.comprador.get_full_name()}",
            'tiempo': tiempo,
            'estado': pedido.estado
        })
    
    # Estadísticas adicionales para ventas
    productos_vendidos = usuario.pedidos_campesino.filter(
        fecha_pedido__range=[inicio_mes, fin_mes],
        estado='completed'
    ).aggregate(total=Sum('detalles__cantidad'))['total'] or 0
    
    clientes_unicos = usuario.pedidos_campesino.filter(
        fecha_pedido__range=[inicio_mes, fin_mes]
    ).values('comprador').distinct().count()
    
    context = {
        'page_title': 'Dashboard Campesino - Campo Directo',
        'user_type': 'campesino',
        'usuario': usuario,
        'estadisticas': {
            'productos_activos': productos_activos,
            'pedidos_pendientes': pedidos_pendientes,
            'ventas_mes': int(ventas_mes),
            'calificacion': calificacion,
            'productos_vendidos': int(productos_vendidos),
            'clientes_unicos': clientes_unicos
        },
        'finca_info': finca_info,
        'actividad_reciente': actividad_reciente
    }
    
    return render(request, 'dashboard.html', context)


def registro_exitoso(request):
    """
    Página de registro exitoso
    """
    context = {
        'page_title': 'Registro Exitoso - Campo Directo'
    }
    return render(request, 'registro-exitoso.html', context)


@ensure_csrf_cookie
def login_comprador(request):
    """
    Página de inicio de sesión para compradores
    """
    context = {
        'page_title': 'Iniciar Sesión Comprador - Campo Directo'
    }
    return render(request, 'login-comprador.html', context)


@login_required
def dashboard_comprador(request):
    """
    Dashboard del comprador - Solo usuarios autenticados
    """
    # Permitir tanto a compradores como a campesinos entrar al marketplace
    if not (request.user.is_comprador or request.user.is_campesino):
        return redirect('frontend:login')
    
    # Renderizar dashboard con datos reales del usuario autenticado
    return render_comprador_dashboard_with_data(request)


def render_comprador_dashboard_with_data(request):
    """
    Renderiza el dashboard del comprador con datos reales
    """
    # Obtener datos del comprador
    usuario = request.user
    
    # Período del mes actual
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    # Estadísticas de pedidos del mes
    pedidos_mes = usuario.pedidos_comprador.filter(
        fecha_pedido__range=[inicio_mes, fin_mes]
    ).count()
    
    # Total gastado en el mes
    total_gastado = usuario.pedidos_comprador.filter(
        fecha_pedido__range=[inicio_mes, fin_mes],
        estado__in=['completed', 'ready']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Campesinos favoritos (campesinos con los que ha hecho más pedidos)
    campesinos_frecuentes = usuario.pedidos_comprador.values('campesino').annotate(
        total_pedidos=Count('id')
    ).count()
    
    # Ahorro total real vs precios de mercado SIPSA
    ahorro_estimado = Decimal('0')
    pedidos_ahorro = usuario.pedidos_comprador.filter(
        estado__in=['completed', 'ready']
    ).prefetch_related('detalles__producto')
    
    for pedido in pedidos_ahorro:
        for detalle in pedido.detalles.all():
            nombre = detalle.producto.nombre
            palabra_clave = nombre.split()[0].strip() if nombre else ''
            
            sipsa_val = None
            if palabra_clave:
                qs = SipsaPrecio.objects.filter(producto__icontains=palabra_clave)
                if qs.exists():
                    palabra_lower = palabra_clave.lower()
                    matches_validos = []
                    for s in qs:
                        if palabra_lower in re.findall(r'\w+', s.producto.lower()):
                            matches_validos.append(s)
                    if matches_validos:
                        matches_exactos = [s for s in matches_validos if s.producto.replace('*', '').strip().lower() in nombre.lower()]
                        if matches_exactos:
                            sipsa_val = matches_exactos[0]
                        else:
                            sipsa_val = max(matches_validos, key=lambda x: x.precio_promedio)
                            
            # Precio estimado en supermercado = SIPSA mayorista × 1.5
            # (el minorista típicamente cobra 40-70% más que el mayoreo)
            if sipsa_val:
                precio_supermercado = sipsa_val.precio_promedio * Decimal('1.5')
                if precio_supermercado > detalle.precio_unitario:
                    ahorro_estimado += (precio_supermercado - detalle.precio_unitario) * detalle.cantidad
    
    # Pedidos activos (no completados)
    pedidos_activos = usuario.pedidos_comprador.filter(
        estado__in=['pending', 'confirmed', 'preparing', 'ready']
    ).count()
    
    # Actividad reciente
    actividad_reciente = []
    pedidos_recientes = usuario.pedidos_comprador.order_by('-fecha_pedido')[:5]
    for pedido in pedidos_recientes:
        tiempo_transcurrido = timezone.now() - pedido.fecha_pedido
        if tiempo_transcurrido.days == 0:
            if tiempo_transcurrido.seconds < 3600:
                tiempo = f"Hace {tiempo_transcurrido.seconds // 60} minutos"
            else:
                tiempo = f"Hace {tiempo_transcurrido.seconds // 3600} horas"
        else:
            tiempo = f"Hace {tiempo_transcurrido.days} día{'s' if tiempo_transcurrido.days > 1 else ''}"
            
        actividad_reciente.append({
            'tipo': 'pedido',
            'descripcion': f"Pedido {pedido.get_estado_display().lower()} - {pedido.campesino.get_full_name()}",
            'tiempo': tiempo,
            'estado': pedido.estado,
            'total': pedido.total
        })
    
    context = {
        'page_title': 'Dashboard Comprador - Campo Directo',
        'user_type': 'comprador',
        'usuario': usuario,
        'estadisticas': {
            'pedidos_mes': pedidos_mes,
            'total_gastado': int(total_gastado),
            'campesinos_favoritos': campesinos_frecuentes,
            'ahorro_total': int(ahorro_estimado),
            'pedidos_activos': pedidos_activos
        },
        'actividad_reciente': actividad_reciente
    }
    
    return render(request, 'dashboard-comprador.html', context)


def dashboard_redirect(request):
    """
    Redirección inteligente al dashboard correcto según tipo de usuario
    """
    if not request.user.is_authenticated:
        return redirect('frontend:login')
    
    if request.user.is_comprador:
        return redirect('frontend:dashboard-comprador')
    else:
        return redirect('frontend:dashboard')


def logout_view(request):
    """
    Vista de logout que limpia la sesión de Django
    """
    logout(request)
    # Redirigir al home con un parámetro de URL especial para que el frontend limpie sus tokens locales
    return redirect('/?logout=true')


@require_http_methods(["GET"])
def health_check_frontend(request):
    """
    Health check para el frontend
    """
    return JsonResponse({
        'status': 'ok',
        'frontend': 'running',
        'templates': 'loaded',
        'static_files': 'configured'
    })
