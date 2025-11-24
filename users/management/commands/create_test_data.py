"""
Comando para crear datos de prueba para el dashboard
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import random

from farms.models import Finca, Certificacion
from products.models import CategoriaProducto, Producto
from orders.models import Pedido, DetallePedido

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos de prueba para los dashboards'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina datos existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Eliminando datos existentes...')
            Pedido.objects.all().delete()
            Producto.objects.all().delete()
            Finca.objects.all().delete()
            CategoriaProducto.objects.all().delete()
            Usuario.objects.filter(is_superuser=False).delete()

        self.stdout.write('Creando datos de prueba...')
        
        # Crear categorías
        categorias = self.crear_categorias()
        
        # Crear usuarios
        campesinos = self.crear_campesinos()
        compradores = self.crear_compradores()
        
        # Crear fincas
        fincas = self.crear_fincas(campesinos)
        
        # Crear productos
        productos = self.crear_productos(campesinos, categorias, fincas)
        
        # Crear pedidos
        self.crear_pedidos(campesinos, compradores, productos)
        
        self.stdout.write(
            self.style.SUCCESS('Datos de prueba creados exitosamente!')
        )

    def crear_categorias(self):
        categorias_data = [
            {'nombre': 'Vegetales', 'icono': '🥬', 'descripcion': 'Vegetales frescos'},
            {'nombre': 'Frutas', 'icono': '🍊', 'descripcion': 'Frutas de temporada'},
            {'nombre': 'Granos', 'icono': '🌾', 'descripcion': 'Granos y cereales'},
            {'nombre': 'Hierbas', 'icono': '🌿', 'descripcion': 'Hierbas aromáticas'},
        ]
        
        categorias = []
        for cat_data in categorias_data:
            categoria, created = CategoriaProducto.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults=cat_data
            )
            categorias.append(categoria)
            if created:
                self.stdout.write(f'Categoría creada: {categoria.nombre}')
        
        return categorias

    def crear_campesinos(self):
        campesinos_data = [
            {
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'email': 'juan.perez@campodirecto.com',
                'telefono': '3101234567',
                'fecha_nacimiento': '1980-05-15',
            },
            {
                'nombre': 'María',
                'apellido': 'González',
                'email': 'maria.gonzalez@campodirecto.com',
                'telefono': '3107654321',
                'fecha_nacimiento': '1975-08-22',
            },
            {
                'nombre': 'Carlos',
                'apellido': 'Rodríguez',
                'email': 'carlos.rodriguez@campodirecto.com',
                'telefono': '3109876543',
                'fecha_nacimiento': '1983-12-10',
            },
        ]
        
        campesinos = []
        for camp_data in campesinos_data:
            campesino, created = Usuario.objects.get_or_create(
                email=camp_data['email'],
                defaults={
                    **camp_data,
                    'tipo_usuario': 'campesino',
                    'calificacion_promedio': Decimal(str(random.uniform(4.0, 5.0))),
                    'total_calificaciones': random.randint(5, 25)
                }
            )
            if created:
                campesino.set_password('testpassword123')
                campesino.save()
                self.stdout.write(f'Campesino creado: {campesino.get_full_name()}')
            campesinos.append(campesino)
        
        return campesinos

    def crear_compradores(self):
        compradores_data = [
            {
                'nombre': 'Ana',
                'apellido': 'Martínez',
                'email': 'ana.martinez@campodirecto.com',
                'telefono': '3201234567',
                'fecha_nacimiento': '1990-03-12',
            },
            {
                'nombre': 'Luis',
                'apellido': 'Hernández',
                'email': 'luis.hernandez@campodirecto.com',
                'telefono': '3207654321',
                'fecha_nacimiento': '1988-07-25',
            },
        ]
        
        compradores = []
        for comp_data in compradores_data:
            comprador, created = Usuario.objects.get_or_create(
                email=comp_data['email'],
                defaults={
                    **comp_data,
                    'tipo_usuario': 'comprador'
                }
            )
            if created:
                comprador.set_password('testpassword123')
                comprador.save()
                self.stdout.write(f'Comprador creado: {comprador.get_full_name()}')
            compradores.append(comprador)
        
        return compradores

    def crear_fincas(self, campesinos):
        fincas_data = [
            {
                'nombre_finca': 'Finca San José',
                'ubicacion_departamento': 'Cundinamarca',
                'ubicacion_municipio': 'La Vega',
                'area_hectareas': Decimal('5.5'),
                'tipo_cultivo': 'organico',
                'descripcion': 'Finca dedicada a cultivos orgánicos'
            },
            {
                'nombre_finca': 'La Esperanza',
                'ubicacion_departamento': 'Boyacá',
                'ubicacion_municipio': 'Villa de Leyva',
                'area_hectareas': Decimal('3.2'),
                'tipo_cultivo': 'hidroponico',
                'descripcion': 'Cultivos hidropónicos de alta calidad'
            },
            {
                'nombre_finca': 'El Paraíso Verde',
                'ubicacion_departamento': 'Antioquia',
                'ubicacion_municipio': 'Rionegro',
                'area_hectareas': Decimal('8.0'),
                'tipo_cultivo': 'tradicional',
                'descripcion': 'Cultivos tradicionales familiares'
            },
        ]
        
        fincas = []
        for i, finca_data in enumerate(fincas_data):
            if i < len(campesinos):
                finca, created = Finca.objects.get_or_create(
                    usuario=campesinos[i],
                    nombre_finca=finca_data['nombre_finca'],
                    defaults=finca_data
                )
                if created:
                    self.stdout.write(f'Finca creada: {finca.nombre_finca}')
                fincas.append(finca)
        
        return fincas

    def crear_productos(self, campesinos, categorias, fincas):
        productos_data = [
            {'nombre': 'Tomates Cherry Orgánicos', 'precio': 8000, 'stock': 25, 'categoria': 'Vegetales'},
            {'nombre': 'Lechugas Hidropónicas', 'precio': 3500, 'stock': 40, 'categoria': 'Vegetales'},
            {'nombre': 'Zanahorias Baby', 'precio': 4500, 'stock': 30, 'categoria': 'Vegetales'},
            {'nombre': 'Fresas Premium', 'precio': 12000, 'stock': 15, 'categoria': 'Frutas'},
            {'nombre': 'Moras Frescas', 'precio': 10000, 'stock': 20, 'categoria': 'Frutas'},
            {'nombre': 'Quinoa Orgánica', 'precio': 15000, 'stock': 10, 'categoria': 'Granos'},
            {'nombre': 'Albahaca Fresca', 'precio': 2500, 'stock': 50, 'categoria': 'Hierbas'},
        ]
        
        productos = []
        for i, prod_data in enumerate(productos_data):
            if i < len(fincas):
                categoria = next((cat for cat in categorias if cat.nombre == prod_data['categoria']), categorias[0])
                
                producto, created = Producto.objects.get_or_create(
                    usuario=fincas[i % len(fincas)].usuario,
                    finca=fincas[i % len(fincas)],
                    nombre=prod_data['nombre'],
                    defaults={
                        'categoria': categoria,
                        'precio_por_kg': Decimal(str(prod_data['precio'])),
                        'stock_disponible': prod_data['stock'],
                        'descripcion': f'Producto fresco de {fincas[i % len(fincas)].nombre_finca}',
                        'calidad': random.choice(['premium', 'primera']),
                        'disponible_entrega_inmediata': True,
                        'peso_minimo_venta': Decimal('0.5'),
                        'peso_maximo_venta': Decimal('10.0'),
                    }
                )
                if created:
                    self.stdout.write(f'Producto creado: {producto.nombre}')
                productos.append(producto)
        
        return productos

    def crear_pedidos(self, campesinos, compradores, productos):
        # Crear pedidos de los últimos 30 días
        for _ in range(15):
            dias_atras = random.randint(0, 30)
            fecha_pedido = timezone.now() - timedelta(days=dias_atras)
            
            comprador = random.choice(compradores)
            campesino = random.choice(campesinos)
            
            # Crear pedido
            pedido = Pedido.objects.create(
                comprador=comprador,
                campesino=campesino,
                total=Decimal('0'),  # Se calculará después
                estado=random.choice(['pending', 'confirmed', 'completed', 'ready']),
                metodo_pago=random.choice(['efectivo', 'transferencia']),
                fecha_pedido=fecha_pedido,
            )
            
            # Agregar productos al pedido
            productos_pedido = random.sample(productos, random.randint(1, 3))
            total_pedido = Decimal('0')
            
            for producto in productos_pedido:
                cantidad = Decimal(str(random.uniform(1, 5)))
                precio_unitario = producto.precio_por_kg
                
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                )
                
                total_pedido += cantidad * precio_unitario
            
            pedido.total = total_pedido
            pedido.save()
        
        self.stdout.write(f'Creados {Pedido.objects.count()} pedidos de prueba')