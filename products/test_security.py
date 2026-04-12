from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from products.models import CategoriaProducto, Producto, SipsaPrecio
from farms.models import Finca

Usuario = get_user_model()

class AdvancedSecurityTests(APITestCase):
    
    def setUp(self):
        # 1. Crear a los actores (Comprador vs Campesinos A y B)
        self.comprador = Usuario.objects.create_user(
            email='comprador@seguridad.test',
            password='password123',
            tipo_usuario='comprador',
            nombre='Mr. Hacker',
            fecha_nacimiento='1990-01-01'
        )
        
        self.campesino_a = Usuario.objects.create_user(
            email='victima@seguridad.test',
            password='password123',
            tipo_usuario='campesino',
            nombre='Campesino Bueno',
            fecha_nacimiento='1980-05-05'
        )
        
        self.campesino_b = Usuario.objects.create_user(
            email='atacante@seguridad.test',
            password='password123',
            tipo_usuario='campesino',
            nombre='Campesino Usurpador',
            fecha_nacimiento='1985-05-05'
        )
        
        # 2. Infraestructura Básica (Finca y Categoría)
        self.categoria, _ = CategoriaProducto.objects.get_or_create(
            nombre='Tubérculos',
            defaults={'estado': 'activo'}
        )
        
        self.finca_victima = Finca.objects.create(
            usuario=self.campesino_a,
            nombre_finca='Finca de Paz',
            area_hectareas=2,
            ubicacion_departamento='Boyaca'
        )
        
        # 3. El Producto de la Víctima (Campesino A)
        self.producto_victima = Producto.objects.create(
            usuario=self.campesino_a,
            finca=self.finca_victima,
            categoria=self.categoria,
            nombre='Papa Criolla Deliciosa',
            precio_por_kg=3000,
            stock_disponible=100,
            unidad_medida='kg'
        )
        
        # 4. Inyectar precio Regulado en Base de Datos DANE (Límite 5000 x 1.3 = 6500)
        SipsaPrecio.objects.get_or_create(
            producto='Papa criolla',
            defaults={'precio_promedio': 5000, 'ciudad': 'Bogota'}
        )
        
        self.url_base = '/api/products/productos/'

    def test_idor_robo_de_recursos(self):
        """
        PRUEBA 1 (IDOR): Verificar que el Campesino B NO pueda borrar el producto del Campesino A.
        """
        # Autenticamos al usurpador
        self.client.force_authenticate(user=self.campesino_b)
        
        # Intentamos destruir el producto de la víctima
        url_borrado = f"{self.url_base}{self.producto_victima.id}/"
        response = self.client.delete(url_borrado)
        
        # El sistema debe bloquearlo por no ser el dueño (IsOwnerOrReadOnly)
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            "¡Fallo IDOR! El Campesino B logró borrar el producto del Campesino A."
        )

    def test_sipsa_blindaje_precios(self):
        """
        PRUEBA 2 (DANE): Verificar que el sistema bloquea los precios absurdos (ej: $600.000)
        en base a la tabla del SIPSA. El tope matemático es $6.500 (5000 x 1.3).
        """
        self.client.force_authenticate(user=self.campesino_a)
        
        payload_abusivo = {
            'nombre': 'Papa criolla',
            'categoria': self.categoria.id,
            'finca': self.finca_victima.id,
            'precio_por_kg': 600000,
            'unidad_medida': 'kg',
            'stock_disponible': 50
        }
        
        response = self.client.post(self.url_base, payload_abusivo, format='json')
        
        # Debe fallar arrojando error 400 de Validación.
        self.assertEqual(
            response.status_code, 
            status.HTTP_400_BAD_REQUEST,
            "¡Fallo de Extorsión! El sistema permitió vender Papas a un precio superior al 1.30X del DANE."
        )
        
        # Confirmar que el mensaje interno es efectivamente una penalidad de precio DANE
        error_dict = response.data
        self.assertIn('precio_por_kg', error_dict)
        self.assertTrue(
            any("Precio demasiado alto" in str(err) for err in error_dict['precio_por_kg']),
            "El producto falló la validación por otro motivo, no por culpa del blindaje SIPSA."
        )
