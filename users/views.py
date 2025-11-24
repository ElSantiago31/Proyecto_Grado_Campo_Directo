"""
Vistas para autenticación y gestión de usuarios
"""

from rest_framework import status, permissions
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
            
            # Generar tokens JWT
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
        serializer = UserDashboardSerializer(request.user)
        return Response(serializer.data)
