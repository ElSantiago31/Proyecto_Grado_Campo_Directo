"""
Comando de gestión de Django para realizar copias de seguridad de la base de datos SQLite.

Uso:
    python manage.py backup_db

Configurar en PythonAnywhere Tasks (cada 24 horas):
    /home/CampoDirecto/virtualenvs/env_campodirecto/bin/python
    /home/CampoDirecto/Proyecto_Grado_Campo_Directo/manage.py backup_db
"""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger('campo_directo')


class Command(BaseCommand):
    help = 'Realiza una copia de seguridad de la base de datos SQLite'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-backups',
            type=int,
            default=7,
            help='Número máximo de backups a conservar (por defecto: 7 días)'
        )

    def handle(self, *args, **options):
        max_backups = options['max_backups']

        # Directorio de backups
        backup_dir = settings.BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)

        # Ruta de la base de datos
        db_path = settings.BASE_DIR / 'db.sqlite3'

        if not db_path.exists():
            self.stderr.write(self.style.ERROR('❌ No se encontró el archivo db.sqlite3'))
            return

        # Nombre del archivo de backup con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.sqlite3'
        backup_path = backup_dir / backup_filename

        try:
            # Copiar la base de datos al directorio de backups
            shutil.copy2(db_path, backup_path)
            size_kb = backup_path.stat().st_size / 1024
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Backup creado: {backup_filename} ({size_kb:.1f} KB)'
                )
            )
            logger.info(f'Backup de BD creado: {backup_filename} ({size_kb:.1f} KB)')

            # Limpiar backups antiguos para no llenar el disco
            self._limpiar_backups_antiguos(backup_dir, max_backups)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ Error creando backup: {str(e)}'))
            logger.error(f'Error creando backup de BD: {str(e)}')

    def _limpiar_backups_antiguos(self, backup_dir: Path, max_backups: int):
        """Elimina los backups más antiguos si se supera el límite."""
        backups = sorted(
            backup_dir.glob('backup_*.sqlite3'),
            key=lambda f: f.stat().st_mtime,
            reverse=True  # Más reciente primero
        )

        if len(backups) > max_backups:
            antiguos = backups[max_backups:]
            for backup in antiguos:
                backup.unlink()
                self.stdout.write(f'🗑️  Backup antiguo eliminado: {backup.name}')
            logger.info(f'Se eliminaron {len(antiguos)} backup(s) antiguos.')
