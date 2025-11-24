#!/usr/bin/env python3
"""
Script para probar el registro de usuarios directo
"""

import requests
import json

def test_registro():
    url = "http://127.0.0.1:8000/api/auth/register/"
    
    data = {
        "nombre": "Test",
        "apellido": "User", 
        "email": "test_6chars_20251020@example.com",
        "password": "Test12",
        "password_confirm": "Test12",
        "telefono": "3001234567",
        "fecha_nacimiento": "1990-01-01",
        "tipo_usuario": "campesino"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        try:
            response_data = response.json()
            print(f"Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

if __name__ == "__main__":
    test_registro()