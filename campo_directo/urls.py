"""
URL configuration for campo_directo project.

Campo Directo - Plataforma que conecta campesinos directamente con compradores
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="Campo Directo API",
        default_version='v1',
        description="API para la plataforma Campo Directo - Conectando campesinos directamente con compradores",
        terms_of_service="https://www.campodirecto.com/terms/",
        contact=openapi.Contact(email="soporte@campodirecto.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


@csrf_exempt
def health_check(request):
    """Endpoint de health check"""
    return JsonResponse({
        'status': 'success',
        'message': 'Campo Directo API está funcionando correctamente',
        'version': '1.0.0',
        'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'Unknown'
    })


def accounts_login_redirect(request):
    """Redirige desde /accounts/login/ a nuestro login personalizado"""
    next_url = request.GET.get('next', '/dashboard-redirect/')
    return redirect(f'/login/?next={next_url}')


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Redirección de accounts/login/ por defecto de Django
    path('accounts/login/', accounts_login_redirect, name='accounts-login-redirect'),
    
    # Health Check
    path('api/health/', health_check, name='health-check'),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API Routes
    path('api/auth/', include('users.urls')),
    path('api/farms/', include('farms.urls')),
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/anti-intermediarios/', include('anti_intermediarios.urls')),
    
    # Frontend Routes
    path('', include('frontend.urls')),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalizar admin
admin.site.site_header = "Campo Directo Admin"
admin.site.site_title = "Campo Directo"
admin.site.index_title = "Administración de Campo Directo"
