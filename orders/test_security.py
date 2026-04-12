from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from orders.models import Pedido
from products.models import Producto, CategoriaProducto
from farms.models import Finca

Usuario = get_user_model()

class OrderSecurityTests(APITestCase):
    
    def setUp(self):
        # 1. Actores
        self.comprador = Usuario.objects.create_user(
            email='comprador@pedidos.test',
            password='password123',
            tipo_usuario='comprador',
            nombre='Comprador Tramposo',
            fecha_nacimiento='1990-01-01'
        )
        self.campesino = Usuario.objects.create_user(
            email='campesino@pedidos.test',
            password='password123',
            tipo_usuario='campesino',
            nombre='Campesino Trabajador',
            fecha_nacimiento='1980-05-05'
        )
        
        # 2. Emular un pedido en estado "Entregado"
        self.pedido = Pedido.objects.create(
            comprador=self.comprador,
            campesino=self.campesino,
            estado='delivered',
            total=50000,
            direccion_entrega='Calle Falsa 123'
        )
        
        self.url = f'/api/orders/pedidos/{self.pedido.id}/'

    def test_maquina_tiempo_integridad_estado(self):
        """
        PRUEBA 3 (INTEGRIDAD DE ESTADOS): Verificar que un comprador no pueda 
        inyectar un PATCH malicioso para devolver el pedido a un estado anterior (pending).
        """
        self.client.force_authenticate(user=self.comprador)
        
        # Intentamos viajar en el tiempo a un estado anterior
        payload_malicioso = {
            'estado': 'pending'
        }
        
        response = self.client.patch(self.url, payload_malicioso, format='json')
        
        # Debe fallar porque la transición Entregado -> Pendiente es ilegal para un comprador
        # Notaremos que devuelve 403 (Prohibido) o 400 (Bad Request), lo cual confirma que estamos protegidos.
        self.assertIn(
            response.status_code, 
            [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
            "¡Fallo de Máquina del Tiempo! El Comprador pudo revertir un pedido que ya había sido Entregado."
        )
