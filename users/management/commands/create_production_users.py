"""
Comando de Django para crear usuarios reales de producción
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import Usuario
from datetime import date
import os


class Command(BaseCommand):
    help = 'Crear usuarios reales para producción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Eliminar usuarios existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== CREANDO USUARIOS DE PRODUCCIÓN ===')
        )
        
        if options['delete_existing']:
            self.stdout.write('Eliminando usuarios existentes...')
            Usuario.objects.filter(email__in=[
                'campesino@campodirecto.com',
                'comprador@campodirecto.com',
                'juan.perez@campodirecto.com',
                'maria.gonzalez@campodirecto.com',
                'admin@campodirecto.com'
            ]).delete()

        usuarios_creados = 0

        with transaction.atomic():
            # 1. CAMPESINO PRINCIPAL
            campesino_principal, created = Usuario.objects.get_or_create(
                email='campesino@campodirecto.com',
                defaults={
                    'nombre': 'Juan Carlos',
                    'apellido': 'Pérez Rodríguez',
                    'telefono': '3123456789',
                    'fecha_nacimiento': date(1975, 3, 15),
                    'tipo_usuario': 'campesino',
                    'estado': 'activo',
                }
            )
            if created:
                campesino_principal.set_password('CampoDirecto2024!')
                campesino_principal.save()
                usuarios_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Campesino creado: {campesino_principal.email}')
                )

            # 2. COMPRADOR PRINCIPAL  
            comprador_principal, created = Usuario.objects.get_or_create(
                email='comprador@campodirecto.com',
                defaults={
                    'nombre': 'María José',
                    'apellido': 'González López',
                    'telefono': '3987654321',
                    'fecha_nacimiento': date(1985, 8, 20),
                    'tipo_usuario': 'comprador',
                    'estado': 'activo',
                }
            )
            if created:
                comprador_principal.set_password('CampoDirecto2024!')
                comprador_principal.save()
                usuarios_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Comprador creado: {comprador_principal.email}')
                )

            # 3. CAMPESINO ADICIONAL
            campesino_demo, created = Usuario.objects.get_or_create(
                email='juan.perez@campodirecto.com',
                defaults={
                    'nombre': 'Juan',
                    'apellido': 'Pérez',
                    'telefono': '3145678901',
                    'fecha_nacimiento': date(1980, 5, 10),
                    'tipo_usuario': 'campesino',
                    'estado': 'activo',
                }
            )
            if created:
                campesino_demo.set_password('Campesino123!')
                campesino_demo.save()
                usuarios_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Campesino adicional: {campesino_demo.email}')
                )

            # 4. COMPRADOR ADICIONAL
            comprador_demo, created = Usuario.objects.get_or_create(
                email='maria.gonzalez@campodirecto.com',
                defaults={
                    'nombre': 'María',
                    'apellido': 'González',
                    'telefono': '3176543210',
                    'fecha_nacimiento': date(1990, 12, 5),
                    'tipo_usuario': 'comprador',
                    'estado': 'activo',
                }
            )
            if created:
                comprador_demo.set_password('Comprador123!')
                comprador_demo.save()
                usuarios_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Comprador adicional: {comprador_demo.email}')
                )

            # 5. SUPERUSUARIO ADMIN
            admin_user, created = Usuario.objects.get_or_create(
                email='admin@campodirecto.com',
                defaults={
                    'nombre': 'Administrador',
                    'apellido': 'Campo Directo',
                    'telefono': '3001234567',
                    'fecha_nacimiento': date(1985, 1, 1),
                    'tipo_usuario': 'comprador',  # Los superusuarios son tipo comprador por defecto
                    'estado': 'activo',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                admin_user.set_password('AdminCampoDirecto2024!')
                admin_user.save()
                usuarios_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Superusuario creado: {admin_user.email}')
                )

        # Mostrar resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'RESUMEN: {usuarios_creados} usuarios nuevos creados'))
        self.stdout.write('='*60)
        
        self.stdout.write(self.style.WARNING('\n📋 CREDENCIALES DE ACCESO PARA PRODUCCIÓN:'))
        self.stdout.write('')
        
        self.stdout.write(self.style.HTTP_INFO('🌱 CAMPESINOS:'))
        self.stdout.write('   • Email: campesino@campodirecto.com')
        self.stdout.write('     Password: CampoDirecto2024!')
        self.stdout.write('   • Email: juan.perez@campodirecto.com') 
        self.stdout.write('     Password: Campesino123!')
        self.stdout.write('')
        
        self.stdout.write(self.style.HTTP_INFO('🛒 COMPRADORES:'))
        self.stdout.write('   • Email: comprador@campodirecto.com')
        self.stdout.write('     Password: CampoDirecto2024!')
        self.stdout.write('   • Email: maria.gonzalez@campodirecto.com')
        self.stdout.write('     Password: Comprador123!')
        self.stdout.write('')
        
        self.stdout.write(self.style.HTTP_INFO('🔧 ADMINISTRADOR:'))
        self.stdout.write('   • Email: admin@campodirecto.com')
        self.stdout.write('     Password: AdminCampoDirecto2024!')
        self.stdout.write('     Acceso: Django Admin + Dashboard')
        self.stdout.write('')
        
        self.stdout.write(self.style.WARNING('⚠️  IMPORTANTE PARA PRODUCCIÓN:'))
        self.stdout.write('   • Cambia las contraseñas después del primer login')
        self.stdout.write('   • Estas credenciales son para configuración inicial')
        self.stdout.write('   • Configura variables de entorno para passwords')
        self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('✅ ¡Usuarios de producción creados exitosamente!'))