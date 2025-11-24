"""
Management command para configurar directorios de media
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Configura los directorios necesarios para almacenar archivos media'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Limpiar directorios existentes antes de crear'
        )

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        
        # Directorios que necesitamos crear
        directories = [
            'users/profiles',
            'products/images', 
            'farms/images',
            'documents',
            'certificates',
            'static/css',
            'static/js',
            'static/images',
            'thumbnails/users',
            'thumbnails/products',
            'thumbnails/farms'
        ]
        
        self.stdout.write(
            self.style.SUCCESS(f'Configurando directorios en: {media_root}')
        )
        
        # Crear directorio raíz de media si no existe
        if not os.path.exists(media_root):
            os.makedirs(media_root)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Directorio raíz creado: {media_root}')
            )
        
        # Crear subdirectorios
        created_count = 0
        for directory in directories:
            dir_path = os.path.join(media_root, directory)
            
            # Limpiar si se solicita
            if options['clean'] and os.path.exists(dir_path):
                import shutil
                shutil.rmtree(dir_path)
                self.stdout.write(
                    self.style.WARNING(f'✗ Directorio eliminado: {directory}')
                )
            
            # Crear directorio
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado: {directory}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'• Ya existe: {directory}')
                )
        
        # Crear archivos .gitkeep para mantener directorios en git
        gitkeep_content = "# Este archivo mantiene el directorio en git\n"
        for directory in directories:
            dir_path = os.path.join(media_root, directory)
            gitkeep_path = os.path.join(dir_path, '.gitkeep')
            
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, 'w') as f:
                    f.write(gitkeep_content)
        
        # Crear archivo .gitignore en media root
        gitignore_path = os.path.join(media_root, '.gitignore')
        gitignore_content = """# Ignorar todos los archivos pero mantener estructura
*
!.gitignore
!*/.gitkeep
"""
        
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Configuración completada!\n'
                f'  • Directorios creados: {created_count}\n'
                f'  • Ubicación: {media_root}\n'
                f'  • Archivos .gitkeep creados para mantener estructura\n'
                f'  • .gitignore configurado'
            )
        )
        
        # Verificar configuración en settings
        self.stdout.write('\n' + '-'*50)
        self.stdout.write('Configuración actual de Django:')
        self.stdout.write(f'  MEDIA_ROOT: {settings.MEDIA_ROOT}')
        self.stdout.write(f'  MEDIA_URL: {settings.MEDIA_URL}')
        self.stdout.write(f'  STATIC_ROOT: {getattr(settings, "STATIC_ROOT", "No configurado")}')
        self.stdout.write(f'  STATIC_URL: {settings.STATIC_URL}')
        
        if hasattr(settings, 'STATICFILES_DIRS'):
            self.stdout.write(f'  STATICFILES_DIRS: {settings.STATICFILES_DIRS}')
        
        # Advertencias
        if not settings.DEBUG:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  ADVERTENCIA: DEBUG está en False. '
                    'Los archivos media deben servirse por el servidor web en producción.'
                )
            )