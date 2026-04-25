import os
import django
from django.conf import settings
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo_directo.settings')
django.setup()

def reset_database():
    print("Iniciando reseteo de la base de datos...")
    
    with connection.cursor() as cursor:
        # 1. Cambiar el charset de la base de datos entera
        db_name = settings.DATABASES['default']['NAME']
        print(f"Alterando charset de la BD: {db_name} a utf8mb4...")
        cursor.execute(f"ALTER DATABASE `{db_name}` CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;")
        
        # 2. Obtener todas las tablas
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("No hay tablas para borrar.")
            return

        # 3. Borrar todas las tablas
        print(f"Borrando {len(tables)} tablas...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for table in tables:
            print(f" - Borrando {table}")
            cursor.execute(f"DROP TABLE IF EXISTS `{table}`;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
    print("¡Proceso completado con éxito! La base de datos está limpia y lista para utf8mb4.")

if __name__ == '__main__':
    reset_database()
