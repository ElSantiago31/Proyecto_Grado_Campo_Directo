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
    ProfileUpdateSerializer, ChangePasswordSerializer, UserDashboardSerializer
)
from .models import Usuario
import json


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
                        'user': UsuarioSerializer(),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(description="Error de validación")
        }
    )
    def post(self, request):
        # Debug: Log de datos recibidos
        print(f"🔍 [DEBUG REGISTRO] Datos recibidos: {json.dumps(request.data, indent=2, default=str)}")
        print(f"🔍 [DEBUG REGISTRO] Content-Type: {request.content_type}")
        print(f"🔍 [DEBUG REGISTRO] Headers: {dict(request.headers)}")
        
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            print(f"✅ [DEBUG REGISTRO] Serializer válido")
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
        
        print(f"❌ [DEBUG REGISTRO] Errores de validación: {json.dumps(serializer.errors, indent=2, default=str)}")
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
                        'user': UsuarioSerializer(),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: openapi.Response(description="Credenciales inválidas")
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Actualizar último login
            user.ultimo_login = timezone.now()
            user.save()
            
            # Crear sesión Django para el usuario (para que funcione con @login_required)
            login(request, user)
            
            # --- PROTECCIÓN ANTI-DUPLICIDAD DE SESIÓN (Producción) ---
            # Si un campesino inicia sesión en Celular B, quemamos los tokens del Celular A
            try:
                from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
                tokens_viejos = OutstandingToken.objects.filter(user=user)
                for token in tokens_viejos:
                    # Añadir a Blacklist revoca instantáneamente su capacidad de ser refrescados
                    BlacklistedToken.objects.get_or_create(token=token)
            except Exception as e:
                import logging
                logging.error(f"Error revocando sesiones antiguas: {str(e)}")
            # --------------------------------------------------------
            
            # Generar tokens JWT nuevos y únicos para este nuevo dispositivo
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Inicio de sesión exitoso',
                'user': UsuarioSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


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

