#!/usr/bin/env python
"""
Script para crear un dump SQL con datos de producción de Campo Directo
Este script permite exportar la base de datos de producción a un archivo SQL
"""

import os
import sys
import django
from django.core.management import execute_from_command_line, call_command
from django.conf import settings
import subprocess
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo_directo.settings')
django.setup()

def create_mysql_dump():
    """
    Crear dump de MySQL de la base de datos de producción
    """
    print("🗄️  Creando dump de MySQL para base de datos de producción...")
    
    # Obtener configuración de la BD de producción
    prod_db_config = settings.DATABASES['production']
    
    db_name = prod_db_config['NAME']
    db_user = prod_db_config['USER']
    db_password = prod_db_config['PASSWORD']
    db_host = prod_db_config['HOST']
    db_port = prod_db_config['PORT']
    
    # Nombre del archivo dump
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_filename = f"campo_directo_production_dump_{timestamp}.sql"
    dump_path = os.path.join(os.getcwd(), "dumps", dump_filename)
    
    # Crear directorio dumps si no existe
    os.makedirs("dumps", exist_ok=True)
    
    # Comando mysqldump
    mysqldump_cmd = [
        "mysqldump",
        f"--host={db_host}",
        f"--port={db_port}",
        f"--user={db_user}",
        f"--password={db_password}",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--add-drop-table",
        "--create-options",
        "--quick",
        "--extended-insert",
        "--complete-insert",
        "--comments",
        "--dump-date",
        db_name
    ]
    
    try:
        print(f"📁 Creando archivo: {dump_path}")
        
        with open(dump_path, 'w', encoding='utf-8') as dump_file:
            # Agregar header personalizado
            header = f"""-- ============================================
-- Campo Directo - Dump de Base de Datos de Producción
-- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Base de datos: {db_name}
-- ============================================
-- Este archivo contiene datos de producción realistas para Campo Directo
-- Incluye: usuarios, fincas, productos, pedidos, certificaciones
-- ============================================

"""
            dump_file.write(header)
            
            # Ejecutar mysqldump
            result = subprocess.run(
                mysqldump_cmd,
                stdout=dump_file,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        
        print(f"✅ Dump creado exitosamente: {dump_path}")
        
        # Mostrar tamaño del archivo
        file_size = os.path.getsize(dump_path) / (1024 * 1024)  # MB
        print(f"📏 Tamaño del archivo: {file_size:.2f} MB")
        
        return dump_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando mysqldump: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return None
    except FileNotFoundError:
        print("❌ Error: mysqldump no encontrado. Instala MySQL client tools.")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def create_django_fixture():
    """
    Crear fixture de Django con datos de producción
    """
    print("📦 Creando fixture de Django...")
    
    try:
        fixture_filename = f"production_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        fixture_path = os.path.join("dumps", fixture_filename)
        
        # Crear directorio dumps si no existe
        os.makedirs("dumps", exist_ok=True)
        
        # Comando dumpdata para la BD de producción
        with open(fixture_path, 'w', encoding='utf-8') as fixture_file:
            call_command(
                'dumpdata',
                'users.Usuario',
                'farms.Finca', 
                'farms.Certificacion',
                'products.CategoriaProducto',
                'products.Producto',
                'orders.Pedido',
                'orders.DetallePedido',
                database='production',
                indent=2,
                stdout=fixture_file
            )
        
        print(f"✅ Fixture creado exitosamente: {fixture_path}")
        
        # Mostrar tamaño del archivo
        file_size = os.path.getsize(fixture_path) / (1024 * 1024)  # MB
        print(f"📏 Tamaño del archivo: {file_size:.2f} MB")
        
        return fixture_path
        
    except Exception as e:
        print(f"❌ Error creando fixture: {e}")
        return None

def show_import_instructions(mysql_dump_path, fixture_path):
    """
    Mostrar instrucciones para importar los datos
    """
    print("\n" + "="*80)
    print("📋 INSTRUCCIONES DE IMPORTACIÓN")
    print("="*80)
    
    if mysql_dump_path:
        print("\n🗄️  IMPORTAR DUMP DE MYSQL:")
        print("   1. Crear base de datos (si no existe):")
        print("      mysql -u root -p -e 'CREATE DATABASE campo_directo_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'")
        print(f"\n   2. Importar dump:")
        print(f"      mysql -u root -p campo_directo_production < {mysql_dump_path}")
        
    if fixture_path:
        print("\n📦 IMPORTAR FIXTURE DE DJANGO:")
        print("   1. Ejecutar migraciones en BD de producción:")
        print("      python manage.py migrate --database=production")
        print(f"\n   2. Cargar fixture:")
        print(f"      python manage.py loaddata {fixture_path} --database=production")
    
    print("\n💡 USAR DATOS DE PRODUCCIÓN EN CÓDIGO:")
    print("   # Consultar datos de producción")
    print("   from campo_directo.routers import ProductionDataManager")
    print("   from users.models import Usuario")
    print("   ")
    print("   # Obtener usuarios de producción")
    print("   usuarios_prod = ProductionDataManager.get_production_queryset(Usuario)")
    print("   ")
    print("   # O usar directamente:")
    print("   productos_prod = Producto.objects.using('production').all()")
    
    print("\n🔧 CONFIGURACIÓN .ENV REQUERIDA:")
    print("   PROD_DB_NAME=campo_directo_production")
    print("   PROD_DB_USER=root")
    print("   PROD_DB_PASSWORD=tu_password")
    print("   PROD_DB_HOST=localhost")
    print("   PROD_DB_PORT=3306")

def main():
    """
    Función principal
    """
    print("🚀 GENERADOR DE DUMP DE PRODUCCIÓN - Campo Directo")
    print("="*60)
    
    # Verificar configuración de BD de producción
    if 'production' not in settings.DATABASES:
        print("❌ Error: Base de datos 'production' no configurada en settings.py")
        sys.exit(1)
    
    mysql_dump_path = None
    fixture_path = None
    
    try:
        # Crear dump de MySQL
        mysql_dump_path = create_mysql_dump()
        
        # Crear fixture de Django
        fixture_path = create_django_fixture()
        
    except Exception as e:
        print(f"❌ Error durante la creación: {e}")
    
    # Mostrar instrucciones
    show_import_instructions(mysql_dump_path, fixture_path)
    
    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    main()