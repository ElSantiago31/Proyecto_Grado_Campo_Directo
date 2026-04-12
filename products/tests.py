from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class ProductoSecurityTests(APITestCase):
    
    def setUp(self):
        # Escenario Base: Construir a los actores de la prueba en la BD simulada
        self.comprador_malicioso = Usuario.objects.create_user(
            email='comprador@seguridad.test',
            password='password123',
            tipo_usuario='comprador',
            nombre='Mr. Hacker',
            fecha_nacimiento='1990-01-01'
        )
        self.url = '/api/products/productos/'

    def test_bfla_comprador_no_puede_crear_producto(self):
        """
        PRUEBA DE SEGURIDAD (BFLA): 
        Verificar que un actor malintencionado que tenga el JWT válido de un "comprador", 
        reciba un HTTP 403 (Prohibido) al intentar inyectar un nuevo producto.
        """
        # 1. Simular inicio de sesión inyectando el token del Comprador
        self.client.force_authenticate(user=self.comprador_malicioso)
        
        # 2. Preparar un cuerpo JSON malicioso intentando publicar un producto
        payload = {
            'nombre': 'Un producto inventado',
            'precio_por_kg': 500,
            'unidad_medida': 'kg',
            'stock_disponible': 100,
        }
        
        # 3. Disparar el ataque contra la API
        response = self.client.post(self.url, payload, format='json')
        
        # 4. Afirmar (Assert) que el escudo funcionó. Si da 201 Created, el test explota.
        self.assertEqual(
            response.status_code, 
            status.HTTP_403_FORBIDDEN,
            "¡Fallo de Seguridad! La API no bloqueó a un Comprador de crear productos."
        )
