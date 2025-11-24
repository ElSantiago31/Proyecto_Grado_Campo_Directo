import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from farms.models import Finca
from products.models import CategoriaProducto, Producto
from orders.models import Pedido, DetallePedido
from anti_intermediarios.models import TransparenciaPrecios
from django.utils import timezone
from decimal import Decimal
from datetime import date

Usuario = get_user_model()

class Command(BaseCommand):
    help = 'Crea datos de prueba para el desarrollo'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de prueba...'))
        
        # Crear categorías de productos
        categoria_frutas, created = CategoriaProducto.objects.get_or_create(
            nombre='Frutas',
            defaults={'descripcion': 'Frutas frescas de temporada'}
        )
        
        categoria_verduras, created = CategoriaProducto.objects.get_or_create(
            nombre='Verduras',
            defaults={'descripcion': 'Verduras y hortalizas frescas'}
        )

        # Crear usuarios campesinos
        campesino1 = self.create_user_if_not_exists(
            email='campesino1@example.com',
            nombre='Juan Carlos',
            apellido='González',
            tipo_usuario='campesino',
            telefono='3101234567'
        )

        campesino2 = self.create_user_if_not_exists(
            email='campesino2@example.com',
            nombre='María Elena',
            apellido='Rodríguez',
            tipo_usuario='campesino',
            telefono='3207654321'
        )

        # Crear usuarios compradores
        comprador1 = self.create_user_if_not_exists(
            email='comprador1@example.com',
            nombre='Ana Sofia',
            apellido='Martínez',
            tipo_usuario='comprador',
            telefono='3151122334'
        )

        comprador2 = self.create_user_if_not_exists(
            email='comprador2@example.com',
            nombre='Carlos Eduardo',
            apellido='López',
            tipo_usuario='comprador',
            telefono='3189876543'
        )

        # Crear fincas
        finca1 = self.create_finca_if_not_exists(
            campesino=campesino1,
            nombre='Finca El Paraíso',
            departamento='Cundinamarca',
            municipio='La Vega',
            direccion='Vereda El Carmen',
            area_hectareas=Decimal('5.5')
        )

        finca2 = self.create_finca_if_not_exists(
            campesino=campesino2,
            nombre='Granja Bella Vista',
            departamento='Boyacá',
            municipio='Villa de Leyva',
            direccion='Vereda Santa Sofia',
            area_hectareas=Decimal('3.2')
        )

        # Crear productos
        productos = [
            {
                'nombre': 'Aguacate Hass',
                'descripcion': 'Aguacates frescos y cremosos, perfectos para consumo directo',
                'precio_por_kg': Decimal('2500'),
                'stock_disponible': 150,
                'unidad_medida': 'unidad',
                'categoria': categoria_frutas,
                'finca': finca1,
                'usuario': campesino1
            },
            {
                'nombre': 'Tomate Cherry',
                'descripcion': 'Tomates cherry orgánicos, ideales para ensaladas',
                'precio_por_kg': Decimal('4000'),
                'stock_disponible': 80,
                'unidad_medida': 'libra',
                'categoria': categoria_verduras,
                'finca': finca1,
                'usuario': campesino1
            },
            {
                'nombre': 'Lechuga Crespa',
                'descripcion': 'Lechuga fresca cultivada sin químicos',
                'precio_por_kg': Decimal('1500'),
                'stock_disponible': 200,
                'unidad_medida': 'unidad',
                'categoria': categoria_verduras,
                'finca': finca2,
                'usuario': campesino2
            },
            {
                'nombre': 'Mango Tommy',
                'descripcion': 'Mangos dulces y jugosos en su punto perfecto',
                'precio_por_kg': Decimal('3000'),
                'stock_disponible': 120,
                'unidad_medida': 'unidad',
                'categoria': categoria_frutas,
                'finca': finca2,
                'usuario': campesino2
            }
        ]

        productos_creados = []
        for producto_data in productos:
            producto, created = Producto.objects.get_or_create(
                nombre=producto_data['nombre'],
                finca=producto_data['finca'],
                defaults=producto_data
            )
            if created:
                self.stdout.write(f'Producto creado: {producto.nombre}')
            productos_creados.append(producto)

        # Crear algunos pedidos de ejemplo
        pedido1, created = Pedido.objects.get_or_create(
            comprador=comprador1,
            campesino=campesino1,
            estado='pending',
            defaults={
                'total': Decimal('15000'),
                'metodo_pago': 'efectivo',
                'direccion_entrega': 'Calle 123 # 45-67, Bogotá'
            }
        )

        if created:
            # Crear detalles del pedido
            DetallePedido.objects.create(
                pedido=pedido1,
                producto=productos_creados[0],  # Aguacate
                cantidad=4,
                precio_unitario=productos_creados[0].precio_por_kg
            )
            DetallePedido.objects.create(
                pedido=pedido1,
                producto=productos_creados[1],  # Tomate Cherry
                cantidad=2,
                precio_unitario=productos_creados[1].precio_por_kg
            )


        # Crear registros de transparencia de precios
        for producto in productos_creados[:2]:  # Solo para los primeros 2 productos
            TransparenciaPrecios.objects.get_or_create(
                producto=producto,
                defaults={
                    'precio_campo_directo': producto.precio_por_kg,
                    'precio_mercado_tradicional': producto.precio_por_kg * Decimal('1.4'),
                    'fuente_precio_referencia': 'SIPSA-DANE',
                    'ciudad_referencia': 'Bogotá'
                }
            )

        self.stdout.write(self.style.SUCCESS('✅ Datos de prueba creados exitosamente!'))
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('📊 Resumen de datos creados:'))
        self.stdout.write(f'- Usuarios: {Usuario.objects.count()}')
        self.stdout.write(f'- Fincas: {Finca.objects.count()}')
        self.stdout.write(f'- Productos: {Producto.objects.count()}')
        self.stdout.write(f'- Pedidos: {Pedido.objects.count()}')
        self.stdout.write(f'- Transparencia de precios: {TransparenciaPrecios.objects.count()}')

    def create_user_if_not_exists(self, email, nombre, apellido, tipo_usuario, telefono):
        """Crea un usuario solo si no existe"""
        user, created = Usuario.objects.get_or_create(
            email=email,
            defaults={
                'nombre': nombre,
                'apellido': apellido,
                'tipo_usuario': tipo_usuario,
                'telefono': telefono,
                'fecha_nacimiento': date(1990, 1, 1),
                'is_active': True
            }
        )
        if created:
            user.set_password('123456')  # Password simple para desarrollo
            user.save()
            self.stdout.write(f'Usuario creado: {user.email} ({tipo_usuario})')
        return user

    def create_finca_if_not_exists(self, campesino, nombre, departamento, municipio, direccion, area_hectareas):
        """Crea una finca solo si no existe"""
        finca, created = Finca.objects.get_or_create(
            usuario=campesino,
            nombre_finca=nombre,
            defaults={
                'ubicacion_departamento': departamento,
                'ubicacion_municipio': municipio,
                'direccion': direccion,
                'area_hectareas': area_hectareas,
                'estado': 'activa'
            }
        )
        if created:
            self.stdout.write(f'Finca creada: {finca.nombre_finca}')
        return finca
