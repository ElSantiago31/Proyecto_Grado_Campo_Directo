"""
Comando para crear datos completos y realistas de producción para Campo Directo
"""

from django.core.management.base import BaseCommand
from django.db import transaction, connections
from django.utils import timezone
from users.models import Usuario
from farms.models import Finca, Certificacion
from products.models import CategoriaProducto, Producto
from orders.models import Pedido, DetallePedido
from datetime import date, timedelta
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Crear datos completos y realistas para producción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Eliminar datos existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        self.using_db = 'production'  # Base de datos a usar
        
        self.stdout.write(
            self.style.SUCCESS('=== CREANDO DATOS COMPLETOS DE PRODUCCIÓN ===')
        )
        self.stdout.write(f'🗄️  Usando base de datos: {self.using_db}')
        
        # Verificar que la BD de producción esté configurada
        try:
            connection = connections[self.using_db]
            connection.ensure_connection()
            self.stdout.write('✅ Conexión a base de datos de producción exitosa')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error conectando a BD de producción: {str(e)}')
            )
            return
        
        if options['delete_existing']:
            self.stdout.write('🗑️ Eliminando datos existentes de producción...')
            # Eliminar en orden correcto por dependencias
            DetallePedido.objects.using(self.using_db).all().delete()
            Pedido.objects.using(self.using_db).all().delete()
            Producto.objects.using(self.using_db).all().delete()
            CategoriaProducto.objects.using(self.using_db).all().delete()
            Certificacion.objects.using(self.using_db).all().delete()
            Finca.objects.using(self.using_db).all().delete()
            # No eliminamos usuarios porque pueden ser compartidos
            self.stdout.write('✅ Datos anteriores eliminados de producción')

        with transaction.atomic(using=self.using_db):
            self.create_users_if_needed()
            self.create_categories()
            self.create_farms()
            self.create_certificates()
            self.create_products()
            self.create_orders()

        self.show_summary()

    def create_users_if_needed(self):
        """Crear usuarios en BD de producción si no existen"""
        self.stdout.write('👥 Verificando usuarios en BD de producción...')
        
        usuarios_data = [
            {
                'email': 'campesino@campodirecto.com',
                'first_name': 'Carlos',
                'last_name': 'Campesino',
                'tipo_usuario': 'campesino',
                'telefono': '3001234567'
            },
            {
                'email': 'juan.perez@campodirecto.com',
                'first_name': 'Juan Carlos',
                'last_name': 'Pérez García',
                'tipo_usuario': 'campesino',
                'telefono': '3107654321'
            },
            {
                'email': 'comprador@campodirecto.com',
                'first_name': 'Ana',
                'last_name': 'Compradora',
                'tipo_usuario': 'comprador',
                'telefono': '3012345678'
            },
            {
                'email': 'maria.gonzalez@campodirecto.com',
                'first_name': 'María',
                'last_name': 'González',
                'tipo_usuario': 'comprador',
                'telefono': '3198765432'
            }
        ]
        
        for user_data in usuarios_data:
            usuario, created = Usuario.objects.using(self.using_db).get_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'tipo_usuario': user_data['tipo_usuario'],
                    'telefono': user_data['telefono'],
                    'is_active': True
                }
            )
            if created:
                # Establecer password por defecto
                if user_data['tipo_usuario'] == 'campesino':
                    usuario.set_password('campesino123')
                else:
                    usuario.set_password('comprador123')
                usuario.save(using=self.using_db)
                self.stdout.write(f'   ✅ {usuario.get_full_name()} ({usuario.tipo_usuario})')

    def create_categories(self):
        """Crear categorías de productos"""
        self.stdout.write('📋 Creando categorías de productos...')
        
        categorias = [
            {'nombre': 'Vegetales', 'descripcion': 'Verduras y hortalizas frescas', 'icono': '🥬'},
            {'nombre': 'Frutas', 'descripcion': 'Frutas frescas de temporada', 'icono': '🍓'},
            {'nombre': 'Granos', 'descripcion': 'Granos y cereales', 'icono': '🌾'},
            {'nombre': 'Hierbas Aromáticas', 'descripcion': 'Hierbas frescas para cocina', 'icono': '🌿'},
            {'nombre': 'Tubérculos', 'descripcion': 'Papas, yuca, ñame y otros tubérculos', 'icono': '🥔'},
            {'nombre': 'Legumbres', 'descripcion': 'Frijoles, lentejas y leguminosas', 'icono': '🫘'},
        ]
        
        for cat_data in categorias:
            categoria, created = CategoriaProducto.objects.using(self.using_db).get_or_create(
                nombre=cat_data['nombre'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'   ✅ {categoria.nombre}')

    def create_farms(self):
        """Crear fincas para los campesinos"""
        self.stdout.write('🏡 Creando fincas...')
        
        campesinos = Usuario.objects.using(self.using_db).filter(tipo_usuario='campesino')
        
        fincas_data = [
            {
                'usuario_email': 'campesino@campodirecto.com',
                'nombre_finca': 'Finca San José',
                'departamento': 'Cundinamarca',
                'municipio': 'Subachoque', 
                'direccion': 'Vereda El Rosal, Km 3 vía La Pradera',
                'area': Decimal('5.5'),
                'tipo': 'organico',
                'descripcion': 'Finca familiar especializada en productos orgánicos certificados. Cultivamos sin químicos desde hace 15 años.',
                'lat': Decimal('4.9265'),
                'lng': Decimal('-74.1745')
            },
            {
                'usuario_email': 'juan.perez@campodirecto.com',
                'nombre_finca': 'El Paraíso Verde',
                'departamento': 'Boyacá',
                'municipio': 'Villa de Leyva',
                'direccion': 'Vereda Ritoque Alto, Finca El Paraíso',
                'area': Decimal('12.0'),
                'tipo': 'mixto',
                'descripcion': 'Finca ubicada en clima frío, especializada en productos de montaña y agricultura sostenible.',
                'lat': Decimal('5.6342'),
                'lng': Decimal('-73.5252')
            }
        ]
        
        for finca_data in fincas_data:
            try:
                usuario = Usuario.objects.using(self.using_db).get(email=finca_data['usuario_email'])
                finca, created = Finca.objects.using(self.using_db).get_or_create(
                    usuario=usuario,
                    nombre_finca=finca_data['nombre_finca'],
                    defaults={
                        'ubicacion_departamento': finca_data['departamento'],
                        'ubicacion_municipio': finca_data['municipio'],
                        'direccion': finca_data['direccion'],
                        'area_hectareas': finca_data['area'],
                        'tipo_cultivo': finca_data['tipo'],
                        'descripcion': finca_data['descripcion'],
                        'latitud': finca_data['lat'],
                        'longitud': finca_data['lng'],
                        'estado': 'activa'
                    }
                )
                if created:
                    self.stdout.write(f'   ✅ {finca.nombre_finca} - {usuario.get_full_name()}')
            except Usuario.DoesNotExist:
                self.stdout.write(f'   ❌ Usuario {finca_data["usuario_email"]} no encontrado')

    def create_certificates(self):
        """Crear certificaciones para las fincas"""
        self.stdout.write('🏆 Creando certificaciones...')
        
        fincas = Finca.objects.using(self.using_db).all()
        
        certificaciones = [
            {
                'nombre': 'Certificación Orgánica',
                'descripcion': 'Certificación de producción orgánica sin uso de químicos sintéticos',
                'entidad': 'BCS ÖKO-GARANTIE Colombia',
                'vigencia_meses': 36
            },
            {
                'nombre': 'Buenas Prácticas Agrícolas (BPA)',
                'descripcion': 'Certificación en buenas prácticas agrícolas del ICA',
                'entidad': 'Instituto Colombiano Agropecuario - ICA',
                'vigencia_meses': 24
            },
            {
                'nombre': 'Comercio Justo',
                'descripcion': 'Certificación de comercio justo y prácticas sostenibles',
                'entidad': 'Fairtrade International',
                'vigencia_meses': 48
            }
        ]
        
        for finca in fincas:
            # Asignar 1-2 certificaciones por finca
            cert_count = random.randint(1, 2)
            certificaciones_seleccionadas = random.sample(certificaciones, cert_count)
            
            for cert_data in certificaciones_seleccionadas:
                fecha_obtencion = date.today() - timedelta(days=random.randint(30, 400))
                fecha_vencimiento = fecha_obtencion + timedelta(days=cert_data['vigencia_meses'] * 30)
                
                certificacion, created = Certificacion.objects.using(self.using_db).get_or_create(
                    finca=finca,
                    nombre=cert_data['nombre'],
                    defaults={
                        'descripcion': cert_data['descripcion'],
                        'entidad_certificadora': cert_data['entidad'],
                        'fecha_obtencion': fecha_obtencion,
                        'fecha_vencimiento': fecha_vencimiento,
                        'estado': 'vigente'
                    }
                )
                if created:
                    self.stdout.write(f'   ✅ {certificacion.nombre} - {finca.nombre_finca}')

    def create_products(self):
        """Crear productos con datos realistas"""
        self.stdout.write('🌱 Creando productos...')
        
        fincas = Finca.objects.using(self.using_db).all()
        categorias = {cat.nombre: cat for cat in CategoriaProducto.objects.using(self.using_db).all()}
        
        productos_data = [
            # Finca San José (Orgánica)
            {
                'finca_nombre': 'Finca San José',
                'productos': [
                    {'nombre': 'Tomates Cherry Orgánicos', 'categoria': 'Vegetales', 'precio': 8500, 'stock': 45, 'descripcion': 'Tomates cherry cultivados orgánicamente, dulces y jugosos'},
                    {'nombre': 'Lechugas Crespa Orgánica', 'categoria': 'Vegetales', 'precio': 3200, 'stock': 80, 'descripcion': 'Lechugas frescas cultivadas sin químicos'},
                    {'nombre': 'Zanahorias Orgánicas', 'categoria': 'Vegetales', 'precio': 4500, 'stock': 35, 'descripcion': 'Zanahorias orgánicas grandes y dulces'},
                    {'nombre': 'Cilantro Fresco', 'categoria': 'Hierbas Aromáticas', 'precio': 2800, 'stock': 60, 'descripcion': 'Cilantro fresco y aromático'},
                    {'nombre': 'Perejil Crespo', 'categoria': 'Hierbas Aromáticas', 'precio': 2500, 'stock': 50, 'descripcion': 'Perejil crespo de excelente calidad'},
                    {'nombre': 'Fresas Orgánicas', 'categoria': 'Frutas', 'precio': 12000, 'stock': 25, 'descripcion': 'Fresas cultivadas orgánicamente, muy dulces'},
                    {'nombre': 'Espinacas Baby', 'categoria': 'Vegetales', 'precio': 6500, 'stock': 30, 'descripcion': 'Espinacas baby tiernas y nutritivas'},
                ]
            },
            # El Paraíso Verde (Mixto - clima frío)
            {
                'finca_nombre': 'El Paraíso Verde',
                'productos': [
                    {'nombre': 'Papas Criolla', 'categoria': 'Tubérculos', 'precio': 3800, 'stock': 120, 'descripcion': 'Papas criollas de montaña, excelente calidad'},
                    {'nombre': 'Habichuela Verde', 'categoria': 'Vegetales', 'precio': 5200, 'stock': 55, 'descripcion': 'Habichuelas tiernas de clima frío'},
                    {'nombre': 'Brócoli Fresco', 'categoria': 'Vegetales', 'precio': 4800, 'stock': 40, 'descripcion': 'Brócoli fresco de excelente calidad'},
                    {'nombre': 'Cebolla Cabezona', 'categoria': 'Vegetales', 'precio': 2200, 'stock': 90, 'descripcion': 'Cebollas frescas y aromáticas'},
                    {'nombre': 'Remolacha', 'categoria': 'Tubérculos', 'precio': 3500, 'stock': 60, 'descripción': 'Remolachas frescas y dulces'},
                    {'nombre': 'Apio', 'categoria': 'Vegetales', 'precio': 4200, 'stock': 35, 'descripcion': 'Apio fresco y crujiente'},
                    {'nombre': 'Frijol Verde', 'categoria': 'Legumbres', 'precio': 6800, 'stock': 45, 'descripcion': 'Frijol verde tierno, ideal para cocinar'},
                    {'nombre': 'Albahaca', 'categoria': 'Hierbas Aromáticas', 'precio': 3500, 'stock': 40, 'descripcion': 'Albahaca fresca muy aromática'},
                ]
            }
        ]
        
        for finca_productos in productos_data:
            try:
                finca = Finca.objects.using(self.using_db).get(nombre_finca=finca_productos['finca_nombre'])
                
                for prod_data in finca_productos['productos']:
                    categoria = categorias.get(prod_data['categoria'])
                    if categoria:
                        # Generar fecha de cosecha reciente
                        fecha_cosecha = date.today() - timedelta(days=random.randint(1, 15))
                        fecha_vencimiento = fecha_cosecha + timedelta(days=random.randint(7, 30))
                        
                        producto, created = Producto.objects.using(self.using_db).get_or_create(
                            usuario=finca.usuario,
                            finca=finca,
                            nombre=prod_data['nombre'],
                            defaults={
                                'categoria': categoria,
                                'descripcion': prod_data['descripcion'],
                                'precio_por_kg': Decimal(str(prod_data['precio'])),
                                'stock_disponible': prod_data['stock'],
                                'unidad_medida': 'kg',
                                'estado': 'disponible',
                                'calidad': 'primera',
                                'fecha_cosecha': fecha_cosecha,
                                'fecha_vencimiento': fecha_vencimiento,
                                'peso_minimo_venta': Decimal('0.5'),
                                'peso_maximo_venta': Decimal('50.0'),
                                'disponible_entrega_inmediata': True,
                                'tiempo_preparacion_dias': random.randint(1, 3),
                                'tags': f"{categoria.nombre.lower()}, fresco, calidad"
                            }
                        )
                        if created:
                            self.stdout.write(f'   ✅ {producto.nombre} - {finca.nombre_finca}')
                            
            except Finca.DoesNotExist:
                self.stdout.write(f'   ❌ Finca {finca_productos["finca_nombre"]} no encontrada')

    def create_orders(self):
        """Crear pedidos históricos y actuales"""
        self.stdout.write('📦 Creando pedidos...')
        
        compradores = Usuario.objects.using(self.using_db).filter(tipo_usuario='comprador')
        campesinos = Usuario.objects.using(self.using_db).filter(tipo_usuario='campesino')
        productos = Producto.objects.using(self.using_db).all()
        
        if not compradores.exists() or not campesinos.exists() or not productos.exists():
            self.stdout.write('   ❌ No hay suficientes datos para crear pedidos')
            return
        
        # Crear pedidos de los últimos 3 meses
        estados_pedidos = ['completed', 'completed', 'completed', 'pending', 'confirmed', 'preparing', 'ready']
        metodos_pago = ['efectivo', 'transferencia', 'tarjeta']
        
        pedidos_creados = 0
        
        for i in range(25):  # Crear 25 pedidos
            comprador = random.choice(compradores)
            campesino = random.choice(campesinos)
            
            # Fecha aleatoria en los últimos 90 días
            dias_atras = random.randint(1, 90)
            fecha_pedido = timezone.now() - timedelta(days=dias_atras)
            
            # Seleccionar productos del campesino
            productos_campesino = productos.filter(usuario=campesino)
            if not productos_campesino.exists():
                continue
                
            try:
                pedido = Pedido.objects.using(self.using_db).create(
                    comprador=comprador,
                    campesino=campesino,
                    total=Decimal('0'),  # Se calculará después
                    estado=random.choice(estados_pedidos),
                    metodo_pago=random.choice(metodos_pago),
                    notas_comprador=f"Pedido para {comprador.get_full_name()}, entrega prioritaria.",
                    direccion_entrega=f"Calle {random.randint(10, 200)} #{random.randint(10, 99)}-{random.randint(10, 99)}, Bogotá",
                    telefono_contacto=comprador.telefono,
                    fecha_entrega_programada=fecha_pedido.date() + timedelta(days=random.randint(1, 5))
                )
                
                # Agregar productos al pedido
                total_pedido = Decimal('0')
                num_productos = random.randint(2, 5)
                productos_seleccionados = random.sample(list(productos_campesino), min(num_productos, productos_campesino.count()))
                
                for producto in productos_seleccionados:
                    cantidad = Decimal(str(random.uniform(1.0, 10.0))).quantize(Decimal('0.5'))
                    precio_unitario = producto.precio_por_kg
                    subtotal = cantidad * precio_unitario
                    
                    # Este modelo se debe crear si existe DetallePedido
                    try:
                        from orders.models import DetallePedido
                        DetallePedido.objects.using(self.using_db).create(
                            pedido=pedido,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            subtotal=subtotal
                        )
                        total_pedido += subtotal
                    except ImportError:
                        # Si no existe DetallePedido, solo actualizamos el total
                        total_pedido += subtotal
                
                # Actualizar total del pedido
                pedido.total = total_pedido
                
                # Establecer fechas según el estado
                if pedido.estado in ['confirmed', 'preparing', 'ready', 'completed']:
                    pedido.fecha_confirmacion = fecha_pedido + timedelta(hours=random.randint(1, 24))
                
                if pedido.estado in ['preparing', 'ready', 'completed']:
                    pedido.fecha_preparacion = pedido.fecha_confirmacion + timedelta(hours=random.randint(1, 48))
                
                if pedido.estado == 'completed':
                    pedido.fecha_completado = pedido.fecha_preparacion + timedelta(hours=random.randint(1, 72))
                    # Agregar calificaciones para pedidos completados
                    pedido.calificacion_comprador = random.randint(4, 5)
                    pedido.calificacion_campesino = random.randint(4, 5)
                    pedido.comentario_calificacion = "Excelente producto y servicio, muy recomendado."
                
                pedido.save(using=self.using_db)
                pedidos_creados += 1
                
                if pedidos_creados <= 5:  # Mostrar solo los primeros 5
                    self.stdout.write(f'   ✅ {pedido.id} - ${pedido.total:,.0f} ({pedido.estado})')
                    
            except Exception as e:
                self.stdout.write(f'   ❌ Error creando pedido: {str(e)}')
                
        self.stdout.write(f'   📦 Total de pedidos creados: {pedidos_creados}')

    def show_summary(self):
        """Mostrar resumen de datos creados"""
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE DATOS DE PRODUCCIÓN CREADOS'))
        self.stdout.write('='*80)
        
        # Contadores usando BD de producción
        usuarios_count = Usuario.objects.using(self.using_db).count()
        campesinos_count = Usuario.objects.using(self.using_db).filter(tipo_usuario='campesino').count()
        compradores_count = Usuario.objects.using(self.using_db).filter(tipo_usuario='comprador').count()
        fincas_count = Finca.objects.using(self.using_db).count()
        categorias_count = CategoriaProducto.objects.using(self.using_db).count()
        productos_count = Producto.objects.using(self.using_db).count()
        productos_disponibles = Producto.objects.using(self.using_db).filter(estado='disponible').count()
        certificaciones_count = Certificacion.objects.using(self.using_db).count()
        pedidos_count = Pedido.objects.using(self.using_db).count()
        pedidos_pendientes = Pedido.objects.using(self.using_db).filter(estado__in=['pending', 'confirmed', 'preparing']).count()
        pedidos_completados = Pedido.objects.using(self.using_db).filter(estado='completed').count()
        
        # Estadísticas de ventas usando BD de producción
        from django.db import models
        total_ventas = Pedido.objects.using(self.using_db).filter(estado='completed').aggregate(
            total=models.Sum('total')
        )['total'] or Decimal('0')
        
        from django.utils import timezone
        mes_actual = timezone.now().replace(day=1)
        ventas_mes_actual = Pedido.objects.using(self.using_db).filter(
            estado='completed',
            fecha_completado__gte=mes_actual
        ).aggregate(total=models.Sum('total'))['total'] or Decimal('0')
        
        # Mostrar estadísticas
        self.stdout.write(f'👥 USUARIOS:')
        self.stdout.write(f'   • Total: {usuarios_count}')
        self.stdout.write(f'   • Campesinos: {campesinos_count}')
        self.stdout.write(f'   • Compradores: {compradores_count}')
        self.stdout.write('')
        
        self.stdout.write(f'🏡 FINCAS Y PRODUCTOS:')
        self.stdout.write(f'   • Fincas: {fincas_count}')
        self.stdout.write(f'   • Categorías: {categorias_count}')
        self.stdout.write(f'   • Productos totales: {productos_count}')
        self.stdout.write(f'   • Productos disponibles: {productos_disponibles}')
        self.stdout.write(f'   • Certificaciones: {certificaciones_count}')
        self.stdout.write('')
        
        self.stdout.write(f'📦 PEDIDOS:')
        self.stdout.write(f'   • Total de pedidos: {pedidos_count}')
        self.stdout.write(f'   • Pedidos pendientes: {pedidos_pendientes}')
        self.stdout.write(f'   • Pedidos completados: {pedidos_completados}')
        self.stdout.write('')
        
        self.stdout.write(f'💰 VENTAS:')
        self.stdout.write(f'   • Total histórico: ${total_ventas:,.0f}')
        self.stdout.write(f'   • Ventas del mes: ${ventas_mes_actual:,.0f}')
        self.stdout.write('')
        
        # Calcular promedios de calificación usando BD de producción
        calificacion_promedio = Pedido.objects.using(self.using_db).filter(
            calificacion_comprador__isnull=False
        ).aggregate(
            promedio=models.Avg('calificacion_comprador')
        )['promedio']
        
        if calificacion_promedio:
            self.stdout.write(f'⭐ CALIFICACIONES:')
            self.stdout.write(f'   • Promedio general: {calificacion_promedio:.1f}/5.0')
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('✅ ¡BASE DE DATOS DE PRODUCCIÓN COMPLETA!'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('💡 DATOS LISTOS PARA:'))
        self.stdout.write('   • Dashboards con estadísticas reales')
        self.stdout.write('   • Sistema de pedidos funcional') 
        self.stdout.write('   • Catálogo de productos completo')
        self.stdout.write('   • Gestión de fincas y certificaciones')
        self.stdout.write('   • Sistema de calificaciones')
        self.stdout.write('')