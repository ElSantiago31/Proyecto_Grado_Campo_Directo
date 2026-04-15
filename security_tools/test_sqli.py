import os
import sys
import django
import json
from django.test import Client

# Agregar el directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo_directo.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection

# Forzar ALLOWED_HOSTS para el Client
settings.ALLOWED_HOSTS = ['*', 'testserver']

User = get_user_model()

def prepare_test_user():
    """Crear un usuario de prueba para bypass de 401"""
    user, created = User.objects.get_or_create(
        email='tester-sqli@example.com',
        defaults={
            'nombre': 'Tester',
            'apellido': 'SQLi',
            'telefono': '3001234567',
            'fecha_nacimiento': '1990-01-01',
            'tipo_usuario': 'campesino',
            'is_active': True
        }
    )
    if not created:
        user.set_password('password123')
        user.save()
    return user

def run_sqli_tests():
    client = Client()
    user = prepare_test_user()
    client.force_login(user)
    
    # Payloads de prueba
    payloads = [
        "' OR '1'='1",
        "'; --",
        "')) OR 1=1 --",
        "' UNION SELECT NULL, NULL, NULL --",
        "1 OR 1=1",
        "admin'--"
    ]
    
    # Endpoints corregidos basado en urls.py
    endpoints = [
        ('/api/products/productos/buscar/', 'q'),
        ('/api/products/productos/', 'categoria'),
        ('/api/farms/fincas/', 'ubicacion_departamento'),
        ('/api/orders/pedidos/buscar_por_codigo/', 'codigo'),
        ('/api/anti-intermediarios/conversaciones/', 'campesino'),
        ('/api/anti-intermediarios/transparencia-precios/', 'producto')
    ]
    
    results = []
    
    print("--- INICIANDO PENTESTING DE INYECCION SQL ---")
    
    for url, param in endpoints:
        print(f"\nProbando endpoint: {url} (Parametro: {param})")
        for payload in payloads:
            try:
                # Simular GET request con el payload
                response = client.get(url, {param: payload})
                status_code = response.status_code
                
                # Criterios de vulnerabilidad:
                # 1. Error 500 (Base de datos rompió por sintaxis SQL)
                vulnerable = "Potencial" if status_code == 500 else "Seguro"
                
                # Si es 500, intentamos ver si hay un error de base de datos específico en el contenido
                content = response.content.decode('utf-8', errors='ignore') if status_code == 500 else ""
                
                results.append({
                    'endpoint': url,
                    'param': param,
                    'payload': payload,
                    'status': status_code,
                    'result': vulnerable
                })
                
                print(f"  Payload: [{payload}] -> Status: {status_code} [{vulnerable}]")
                
            except Exception as e:
                print(f"  ERROR Critico con Payload [{payload}]: {str(e)}")
                results.append({
                    'endpoint': url,
                    'param': param,
                    'payload': payload,
                    'status': 'EXCEPTION',
                    'result': 'ERROR CRITICO'
                })

    # Resumen final (Sin emojis para evitar errores de codificación en Windows)
    print("\n--- RESUMEN DE RESULTADOS ---")
    vulnerabilities = [r for r in results if r['result'] == "Potencial"]
    
    if vulnerabilities:
        print(f"ALERTA: Se detectaron {len(vulnerabilities)} comportamiento(s) sospechoso(s).")
        for v in vulnerabilities:
            print(f"  - {v['endpoint']} ({v['param']}): {v['payload']} -> {v['status']}")
    else:
        print("RESULTADO: No se detectaron vulnerabilidades de SQL Injection directas.")
        print("El ORM de Django (v5.x) esta protegiendo correctamente las consultas.")

if __name__ == "__main__":
    try:
        run_sqli_tests()
    except Exception as e:
        print(f"No se pudo iniciar la prueba: {e}")
