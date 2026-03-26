"""
Custom middleware for Campo Directo project
"""
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt


class DisableCSRFForAPIMiddleware(MiddlewareMixin):
    """
    Disable CSRF validation for API endpoints that start with /api/
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            print(f"[MIDDLEWARE] Deshabilitando CSRF para la ruta: {request.path}")
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None
