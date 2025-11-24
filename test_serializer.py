import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campo_directo.settings')
django.setup()

from users.serializers import RegisterSerializer

def test_serializer():
    data = {
        'nombre': 'Test',
        'apellido': 'User', 
        'email': 'test-unique@test.com',  # Email único
        'telefono': '3001234567',
        'tipo_usuario': 'campesino',
        'fecha_nacimiento': '1990-01-01',
        'password': 'Test123456',
        'password_confirm': 'Test123456',
        'nombre_finca': 'Finca Test'
    }
    
    print("🧪 Probando RegisterSerializer con datos:")
    print(data)
    print("\n" + "="*50)
    
    # Probar el serializer
    serializer = RegisterSerializer(data=data)
    
    print(f"📋 Es válido: {serializer.is_valid()}")
    
    if not serializer.is_valid():
        print(f"❌ Errores de validación:")
        for field, errors in serializer.errors.items():
            print(f"  - {field}: {errors}")
    else:
        print("✅ Serializer es válido")
        try:
            user = serializer.save()
            print(f"✅ Usuario creado: {user}")
        except Exception as e:
            print(f"❌ Error al crear usuario: {e}")

if __name__ == "__main__":
    test_serializer()