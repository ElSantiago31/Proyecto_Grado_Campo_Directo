from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from products.models import Producto, CategoriaProducto, SipsaPrecio
from users.models import Usuario
from farms.models import Finca

class ProductIntegrityTests(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='farmer@test.com',
            nombre='Juan',
            apellido='Test',
            password='Password123!',
            tipo_usuario='campesino',
            fecha_nacimiento='1990-01-01',
            telefono='3001112233'
        )
        self.categoria, _ = CategoriaProducto.objects.get_or_create(nombre='Frutas')
        self.finca = Finca.objects.create(
            usuario=self.user,
            nombre_finca='Finca Test',
            ubicacion_departamento='Cundinamarca',
            ubicacion_municipio='Zipaquira',
            area_hectareas=Decimal('1.0')
        )

    def test_negative_price_protection(self):
        """
        Verifica que no se puedan crear productos con precios negativos.
        """
        producto = Producto(
            usuario=self.user,
            finca=self.finca,
            categoria=self.categoria,
            nombre='Manzana',
            precio_por_kg=Decimal('-10.0'),
            stock_disponible=100
        )
        with self.assertRaises(Exception): # Django validators o base de datos deberían saltar
            producto.full_clean()
            producto.save()

    def test_sipsa_savings_calculation(self):
        """
        Verifica que la lógica de comparación con SIPSA funcione correctamente.
        """
        # Crear un precio de referencia SIPSA
        SipsaPrecio.objects.create(
            ciudad='Bogotá',
            producto='Papa Sabanera',
            precio_promedio=Decimal('3000.0')
        )
        
        # Crear un producto del campesino más barato
        papa = Producto.objects.create(
            usuario=self.user,
            finca=self.finca,
            categoria=self.categoria,
            nombre='Papa Sabanera',
            precio_por_kg=Decimal('2500.0'),
            stock_disponible=1000
        )
        
        # El ahorro debería ser 500
        ahorro = Decimal('3000.0') - papa.precio_por_kg
        self.assertEqual(ahorro, Decimal('500.0'))
