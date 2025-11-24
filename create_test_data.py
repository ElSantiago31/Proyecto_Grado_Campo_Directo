#!/usr/bin/env python
"""
Script para crear datos de prueba en SQLite
"""
import os
import django
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo_directo.settings')
django.setup()

from django.contrib.auth import get_user_model
from farms.models import Finca
from products.models import CategoriaProducto

Usuario = get_user_model()

def main():
    print('=== CREANDO DATOS DE PRUEBA EN SQLITE ===')
    
    # Crear usuario campesino
    campesino, created = Usuario.objects.get_or_create(
        email='campesino@campodirecto.com',
        defaults={
            'nombre': 'Juan Carlos',
            'apellido': 'Pérez Rodríguez',
            'telefono': '3001234567',
            'tipo_usuario': 'campesino',
            'fecha_nacimiento': date(1985, 5, 15),
        }
    )
    if created:
        campesino.set_password('campodirecto123')
        campesino.save()
        print(f'✓ Campesino creado: {campesino.get_full_name()}')
    else:
        print(f'✓ Campesino ya existe: {campesino.get_full_name()}')

    # Crear usuario comprador
    comprador, created = Usuario.objects.get_or_create(
        email='comprador@campodirecto.com',
        defaults={
            'nombre': 'María José',
            'apellido': 'González López',
            'telefono': '3109876543',
            'tipo_usuario': 'comprador',
            'fecha_nacimiento': date(1990, 8, 22),
        }
    )
    if created:
        comprador.set_password('campodirecto123')
        comprador.save()
        print(f'✓ Comprador creado: {comprador.get_full_name()}')
    else:
        print(f'✓ Comprador ya existe: {comprador.get_full_name()}')

    # Crear finca para el campesino
    finca, created = Finca.objects.get_or_create(
        usuario=campesino,
        nombre_finca='Finca El Progreso',
        defaults={
            'ubicacion_departamento': 'Boyacá',
            'ubicacion_municipio': 'Villa de Leyva',
            'direccion': 'Vereda Santa Sofia, Km 3 vía Chiquinquirá',
            'area_hectareas': 3.8,
            'tipo_cultivo': 'organico',
            'estado': 'activa',
            'descripcion': 'Finca dedicada al cultivo orgánico de hortalizas y frutas'
        }
    )
    if created:
        print(f'✓ Finca creada: {finca.nombre_finca} (ID: {finca.id})')
    else:
        print(f'✓ Finca ya existe: {finca.nombre_finca} (ID: {finca.id})')

    # Crear categorías
    categorias = [
        {'nombre': 'Vegetales y Hortalizas', 'descripcion': 'Verduras frescas y hortalizas', 'icono': '🥬'},
        {'nombre': 'Frutas', 'descripcion': 'Frutas frescas de temporada', 'icono': '🍎'},
        {'nombre': 'Granos y Cereales', 'descripcion': 'Granos y cereales diversos', 'icono': '🌾'},
        {'nombre': 'Hierbas Aromáticas', 'descripcion': 'Hierbas frescas y especias', 'icono': '🌿'},
        {'nombre': 'Tubérculos', 'descripcion': 'Papas, yuca y otros tubérculos', 'icono': '🥔'},
        {'nombre': 'Legumbres', 'descripcion': 'Fríjoles, lentejas y legumbres', 'icono': '🫘'}
    ]

    created_count = 0
    for cat_data in categorias:
        categoria, created = CategoriaProducto.objects.get_or_create(
            nombre=cat_data['nombre'],
            defaults=cat_data
        )
        if created:
            created_count += 1
            print(f'✓ Categoría creada: {categoria.nombre} (ID: {categoria.id})')
        else:
            print(f'✓ Categoría ya existe: {categoria.nombre} (ID: {categoria.id})')

    print()
    print(f'=== RESUMEN ===')
    print(f'Usuarios: {Usuario.objects.count()}')
    print(f'Campesinos: {Usuario.objects.filter(tipo_usuario="campesino").count()}')
    print(f'Fincas: {Finca.objects.count()}')
    print(f'Categorías: {CategoriaProducto.objects.count()}')
    print()
    print('✅ Datos de prueba creados exitosamente!')
    print()
    print('Credenciales para probar:')
    print('- Campesino: campesino@campodirecto.com / campodirecto123')
    print('- Comprador: comprador@campodirecto.com / campodirecto123')

if __name__ == '__main__':
    main()