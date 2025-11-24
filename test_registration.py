#!/usr/bin/env python3
"""
Simple test script to verify the registration endpoint
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_registration():
    # Test data
    test_data = {
        "nombre": "Test Usuario",
        "apellido": "Test Apellido",
        "email": "test_nuevo_usuario@test.com",
        "telefono": "3001234567",
        "tipo_usuario": "comprador",
        "fecha_nacimiento": "1990-01-01",
        "password": "TestPassword123",
        "password_confirm": "TestPassword123"
    }
    
    print("🧪 Testing registration endpoint...")
    print(f"📤 Sending payload: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            return True
        else:
            print("❌ Registration failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"💥 Request failed: {e}")
        return False
    except json.JSONDecodeError:
        print(f"💥 Invalid JSON response: {response.text}")
        return False

if __name__ == "__main__":
    test_registration()