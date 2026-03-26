#!/usr/bin/env python
"""linea de comando de administración de django"""
import os
import sys


def main():
    """correr tareas administrativas de django"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo_directo.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()