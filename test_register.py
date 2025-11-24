import requests
import json

def test_register():
    url = "http://127.0.0.1:8000/api/auth/register/"
    
    data = {
        'nombre': 'Test',
        'apellido': 'User', 
        'email': 'test@test.com',
        'telefono': '3001234567',
        'tipo_usuario': 'campesino',
        'fecha_nacimiento': '1990-01-01',
        'password': 'Test123456',
        'password_confirm': 'Test123456',
        'nombre_finca': 'Finca Test'
    }
    
    print("🧪 Probando registro con datos:")
    print(json.dumps(data, indent=2))
    print("\n" + "="*50)
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"📋 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print("\n📋 Respuesta del servidor:")
        
        try:
            json_response = response.json()
            print(json.dumps(json_response, indent=2, ensure_ascii=False))
        except:
            print(response.text)
            
        if response.status_code == 400:
            print("\n❌ Error de validación encontrado!")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_register()