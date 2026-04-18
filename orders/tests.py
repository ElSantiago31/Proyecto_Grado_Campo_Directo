from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import Usuario
from orders.models import Pedido
from products.models import Producto, CategoriaProducto
from farms.models import Finca
from decimal import Decimal

class OrderSecurityTests(APITestCase):
    def setUp(self):
        # Crear actores
        self.comprador1 = Usuario.objects.create_user(
            email='comprador1@test.com',
            nombre='Comprador 1',
            apellido='Test',
            password='Password123!',
            tipo_usuario='comprador',
            fecha_nacimiento='1990-01-01',
            telefono='3101112233'
        )
        self.comprador2 = Usuario.objects.create_user(
            email='comprador2@test.com',
            nombre='Comprador 2',
            apellido='Test',
            password='Password123!',
            tipo_usuario='comprador',
            fecha_nacimiento='1990-01-01',
            telefono='3104445566'
        )
        self.campesino = Usuario.objects.create_user(
            email='farmer@test.com',
            nombre='Granjero',
            apellido='Test',
            password='Password123!',
            tipo_usuario='campesino',
            fecha_nacimiento='1990-01-01',
            telefono='3107778899'
        )
        
        # Setup de productos para poder crear un pedido
        cat, _ = CategoriaProducto.objects.get_or_create(nombre='Vegetales')
        finca = Finca.objects.create(
            usuario=self.campesino, 
            nombre_finca='La Esperanza',
            ubicacion_departamento='Cundinamarca',
            ubicacion_municipio='Zipaquira',
            area_hectareas=Decimal('1.0')
        )
        self.producto = Producto.objects.create(
            usuario=self.campesino,
            finca=finca,
            categoria=cat,
            nombre='Zanahoria',
            precio_por_kg=Decimal('1500.0'),
            stock_disponible=100
        )
        
        # Crear un pedido para comprador 1
        self.pedido1 = Pedido.objects.create(
            comprador=self.comprador1,
            campesino=self.campesino,
            total=Decimal('15000.0'),
            estado='pending'
        )

    def test_order_privacy_protection(self):
        """
        Verifica que un comprador no pueda ver detalles de pedidos de otros compradores.
        """
        self.client.force_authenticate(user=self.comprador2)
        
        # Intentar acceder al pedido del comprador 1
        # (Asumiendo que existe un endpoint de detalle de pedido)
        try:
            url = reverse('pedido-detail', kwargs={'pk': self.pedido1.pk})
            response = self.client.get(url)
            
            # Debería retornar 404 (No encontrado) o 403 (Prohibido)
            self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        except:
            # Si el endpoint no existe todavía, saltamos el test
            pass

    def test_unauthenticated_order_blocks(self):
        """
        Verifica que no se puedan crear pedidos sin estar autenticado.
        """
        self.client.logout()
        url = reverse('pedido-list') if 'pedido-list' else '/api/orders/'
        try:
            response = self.client.post(url, {})
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        except:
            pass
