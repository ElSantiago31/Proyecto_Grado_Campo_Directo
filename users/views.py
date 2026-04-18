"""
Vistas para autenticación y gestión de usuarios
"""

from rest_framework import status, permissions, parsers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import update_session_auth_hash, login
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    RegisterSerializer, LoginSerializer, UsuarioSerializer,
    ProfileUpdateSerializer, ChangePasswordSerializer, UserDashboardSerializer,
    PinRecoveryRequestSerializer, PinResetSerializer
)
from .models import Usuario
import json
import logging
import traceback

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    """
    Vista para registro de nuevos usuarios
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Registro de nuevo usuario",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="Usuario registrado exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description="Datos del usuario"),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(description="Error de validación")
        }
    )
    def post(self, request):

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Crear sesión Django para el usuario (para que de los permisos de @login_required)
            login(request, user)
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Usuario registrado exitosamente',
                'user': UsuarioSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    Vista para inicio de sesión
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Iniciar sesión",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login exitoso",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description="Datos del usuario"),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: openapi.Response(description="Credenciales inválidas")
        }
    )
    def post(self, request):
        try:
            # Log de depuración inicial (visible en consola/stdout)
            print(f"DEBUG LOGIN: Intento recibido para: {request.data.get('email')}")
            logger.info(f"Iniciando post() de LoginView para: {request.data.get('email')}")

            serializer = LoginSerializer(data=request.data, context={'request': request})
            
            # Capturar errores específicamente en la validación do-or-die
            try:
                is_valid = serializer.is_valid()
            except Exception as val_error:
                error_trace = traceback.format_exc()
                print(f"DEBUG LOGIN: Error en is_valid(): {str(val_error)}")
                logger.error(f"Error durante validación de serializer: {str(val_error)}\n{error_trace}")
                return Response({'error': 'Error de validación interna del servidor'}, status=500)

            if is_valid:
                user = serializer.validated_data['user']
                
                # Actualizar último login
                try:
                    user.ultimo_login = timezone.now()
                    user.save(update_fields=['ultimo_login'])
                except Exception as save_error:
                    logger.warning(f"No se pudo actualizar ultimo_login: {str(save_error)}")
                
                # Crear sesión Django
                try:
                    login(request, user)
                except Exception as login_err:
                    logger.warning(f"Fallo login(request, user): {str(login_err)}")
                
                # --- PROTECCIÓN ANTI-DUPLICIDAD ---
                try:
                    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
                    tokens_viejos = OutstandingToken.objects.filter(user=user)
                    for token in tokens_viejos:
                        BlacklistedToken.objects.get_or_create(token=token)
                except (ImportError, Exception) as e:
                    logger.warning(f"Omitiendo revocación de sesiones antiguas: {str(e)}")
                
                # Generar tokens JWT
                refresh = RefreshToken.for_user(user)
                
                logger.info(f"Login exitoso para: {user.email}")
                return Response({
                    'message': 'Inicio de sesión exitoso',
                    'user': UsuarioSerializer(user).data,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }, status=status.HTTP_200_OK)
                
            logger.warning(f"Login fallido (400) para: {request.data.get('email')} - Errores: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"DEBUG LOGIN CRITICAL: {error_details}")
            logger.error(f"ERROR CRÍTICO EN LOGIN: {str(e)}\n{error_details}")
            return Response({
                'error': 'Error interno del servidor en el proceso de login',
                'detail': str(e) if settings.DEBUG else 'Contacte al administrador'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileView(APIView):
    """
    Vista para obtener información del perfil del usuario autenticado
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Obtener perfil del usuario actual",
        responses={200: UsuarioSerializer()}
    )
    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)


class CurrentUserView(APIView):
    """
    Alias para ProfileView - información del usuario actual
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)


class UpdateProfileView(APIView):
    """
    Vista para actualizar el perfil del usuario
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    @swagger_auto_schema(
        operation_description="Actualizar perfil del usuario",
        request_body=ProfileUpdateSerializer,
        responses={
            200: UsuarioSerializer(),
            400: openapi.Response(description="Error de validación")
        }
    )
    def put(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Perfil actualizado exitosamente',
                'user': UsuarioSerializer(request.user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Vista para cambiar la contraseña del usuario
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Cambiar contraseña del usuario",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Contraseña cambiada exitosamente",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: openapi.Response(description="Error de validación")
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Cambiar la contraseña
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Mantener la sesión activa
            update_session_auth_hash(request, user)
            
            return Response({
                'message': 'Contraseña cambiada exitosamente'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDashboardView(APIView):
    """
    Vista para obtener información del dashboard del usuario
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Obtener información del dashboard del usuario",
        responses={200: UserDashboardSerializer()}
    )
    def get(self, request):
        period = request.query_params.get('period', 'month')
        serializer = UserDashboardSerializer(request.user, context={'request': request, 'period': period})
        return Response(serializer.data)


class CampesinoResenasView(APIView):
    """
    Vista pública para obtener las reseñas/comentarios recibidos por un campesino
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            campesino = Usuario.objects.get(pk=pk, tipo_usuario='campesino')
        except Usuario.DoesNotExist:
            return Response({'error': 'Productor no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        from orders.models import Pedido
        pedidos = Pedido.objects.filter(
            campesino=campesino,
            estado='completed',
            calificacion_comprador__isnull=False
        ).select_related('comprador').prefetch_related('detalles').order_by('-fecha_completado')

        resenas = []
        for pedido in pedidos:
            comprador = pedido.comprador
            nombre = comprador.get_full_name() if comprador else 'Comprador'
            partes = nombre.strip().split()
            nombre_corto = partes[0] + ' ' + partes[-1][0] + '.' if len(partes) > 1 else nombre

            # Obtener nombres de los productos comprados en este pedido
            productos_comprados = [
                d.nombre_producto_snapshot or d.producto.nombre
                for d in pedido.detalles.all()
            ]

            resenas.append({
                'calificacion': pedido.calificacion_comprador,
                'comentario': pedido.comentario_calificacion or '',
                'comprador_nombre': nombre_corto,
                'fecha': pedido.fecha_completado.strftime('%d/%m/%Y') if pedido.fecha_completado else '',
                'productos': productos_comprados,
            })

        # Calcular promedio real desde los pedidos
        total_real = len(resenas)
        promedio_real = sum(r['calificacion'] for r in resenas) / total_real if total_real > 0 else 0.0

        return Response({
            'campesino': campesino.get_full_name(),
            'calificacion_promedio': round(promedio_real, 1),
            'total_calificaciones': total_real,
            'resenas': resenas
        })

class MisResenasCompradorView(APIView):
    """
    Vista para que el comprador vea las reseñas que le dejaron los campesinos
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from orders.models import Pedido
        pedidos = Pedido.objects.filter(
            comprador=request.user,
            estado='completed',
            calificacion_campesino__isnull=False
        ).select_related('campesino').order_by('-fecha_completado')

        resenas = []
        for pedido in pedidos:
            campesino = pedido.campesino
            nombre = campesino.get_full_name() if campesino else 'Productor'
            partes = nombre.strip().split()
            nombre_corto = partes[0] + ' ' + partes[-1][0] + '.' if len(partes) > 1 else nombre

            resenas.append({
                'calificacion': pedido.calificacion_campesino,
                'comentario': pedido.comentario_calificacion or '',
                'campesino_nombre': nombre_corto,
                'fecha': pedido.fecha_completado.strftime('%d/%m/%Y') if pedido.fecha_completado else '',
            })

        # Calcular promedio REAL desde los pedidos, no desde el campo del modelo
        # (el campo del modelo pudo ser poblado por datos de prueba)
        total_real = len(resenas)
        if total_real > 0:
            promedio_real = sum(r['calificacion'] for r in resenas) / total_real
        else:
            promedio_real = 0.0

        return Response({
            'comprador': request.user.get_full_name(),
            'calificacion_promedio': round(promedio_real, 1),
            'total_calificaciones': total_real,
            'resenas': resenas
        })


class PinRecoveryRequestView(APIView):
    """
    Vista para solicitar el código de recuperación de PIN Visual
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PinRecoveryRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = Usuario.objects.get(email=email)
            
            # Generar código de 6 dígitos
            import random
            from django.utils import timezone
            from datetime import timedelta
            from django.core.mail import send_mail
            from django.conf import settings
            
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            user.pin_recovery_code = code
            user.pin_recovery_expires = timezone.now() + timedelta(minutes=15)
            user.save()
            
            # Enviar correo
            subject = 'Código de recuperación de PIN Visual - Campo Directo'
            message = f'Hola {user.nombre},\n\n' \
                      f'Has solicitado recuperar tu PIN Visual (Emoji de Seguridad).\n' \
                      f'Tu código de verificación es: {code}\n\n' \
                      f'Este código expirará en 15 minutos.\n\n' \
                      f'Si no solicitaste este cambio, por favor ignora este correo.'
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return Response({'message': 'Código enviado exitosamente a tu correo.'})
            except Exception as e:
                return Response(
                    {'error': 'Error al enviar el correo. Por favor intenta más tarde.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PinResetView(APIView):
    """
    Vista para restablecer el PIN Visual usando el código de verificación
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PinResetSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_pin = serializer.validated_data['new_pin']
            
            # Actualizar PIN y limpiar campos de recuperación
            user.imagen_2fa = new_pin
            user.pin_recovery_code = None
            user.pin_recovery_expires = None
            
            # Resetear intentos de bloqueo si existían
            user.intentos_2fa_fallidos = 0
            user.bloqueado_2fa_hasta = None
            
            user.save()
            
            return Response({'message': 'Tu PIN Visual ha sido restablecido exitosamente. Ya puedes iniciar sesión.'})
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

