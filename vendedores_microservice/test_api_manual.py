#!/usr/bin/env python3
"""
Script de pruebas manuales para la API de Vendedores
HU KAN-83: Registrar vendedor

Uso:
    python test_api_manual.py

Asegúrate de tener el microservicio corriendo en http://localhost:5002
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:5002"

def print_section(title: str):
    """Imprime un separador de sección."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_response(response: requests.Response):
    """Imprime la respuesta de la API de forma legible."""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_crear_vendedor_exitoso():
    """Test 1: Crear vendedor con todos los campos válidos."""
    print_section("TEST 1: Crear vendedor exitoso")
    
    payload = {
        "nombre": "Juan Carlos",
        "apellidos": "Pérez García",
        "correo": "juan.perez@medisupply.com",
        "celular": "3001234567",
        "telefono": "6015551234",
        "zona": "Bogotá - Colombia",
        "usuario_creacion": "admin@system.com"
    }
    
    print("Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    response = requests.post(f"{BASE_URL}/vendedores", json=payload)
    print_response(response)
    
    if response.status_code == 201:
        return response.json()["id"]
    return None

def test_crear_vendedor_sin_telefono():
    """Test 2: Crear vendedor sin teléfono (campo opcional)."""
    print_section("TEST 2: Crear vendedor sin teléfono (opcional)")
    
    payload = {
        "nombre": "María",
        "apellidos": "López Silva",
        "correo": "maria.lopez@medisupply.com",
        "celular": "3009876543",
        "zona": "Medellín - Colombia"
    }
    
    print("Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    response = requests.post(f"{BASE_URL}/vendedores", json=payload)
    print_response(response)

def test_crear_vendedor_correo_invalido():
    """Test 3: Intentar crear vendedor con correo inválido."""
    print_section("TEST 3: Error - Correo inválido")
    
    payload = {
        "nombre": "Carlos",
        "apellidos": "Gómez",
        "correo": "correo-sin-arroba",
        "celular": "3005555555"
    }
    
    print("Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    response = requests.post(f"{BASE_URL}/vendedores", json=payload)
    print_response(response)

def test_crear_vendedor_celular_corto():
    """Test 4: Intentar crear vendedor con celular muy corto."""
    print_section("TEST 4: Error - Celular muy corto (menos de 10 dígitos)")
    
    payload = {
        "nombre": "Ana",
        "apellidos": "Martínez",
        "correo": "ana.martinez@medisupply.com",
        "celular": "123456"
    }
    
    print("Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    response = requests.post(f"{BASE_URL}/vendedores", json=payload)
    print_response(response)

def test_crear_vendedor_duplicado():
    """Test 5: Intentar crear vendedor con correo duplicado."""
    print_section("TEST 5: Error - Correo duplicado")
    
    payload = {
        "nombre": "Otro Usuario",
        "apellidos": "Apellidos",
        "correo": "juan.perez@medisupply.com",  # Ya existe del Test 1
        "celular": "3007777777"
    }
    
    print("Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    response = requests.post(f"{BASE_URL}/vendedores", json=payload)
    print_response(response)

def test_crear_vendedor_campos_faltantes():
    """Test 6: Intentar crear vendedor sin campos obligatorios."""
    print_section("TEST 6: Error - Campos obligatorios faltantes")
    
    payload = {
        "nombre": "Pedro",
        "apellidos": "Ramírez"
        # Faltan: correo, celular
    }
    
    print("Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    response = requests.post(f"{BASE_URL}/vendedores", json=payload)
    print_response(response)

def test_obtener_vendedor(vendedor_id: str):
    """Test 7: Obtener un vendedor por ID."""
    print_section("TEST 7: Obtener vendedor por ID")
    
    print(f"GET /vendedores/{vendedor_id}")
    print()
    
    response = requests.get(f"{BASE_URL}/vendedores/{vendedor_id}")
    print_response(response)

def test_actualizar_vendedor(vendedor_id: str):
    """Test 8: Actualizar un vendedor."""
    print_section("TEST 8: Actualizar vendedor")
    
    payload = {
        "zona": "Cali - Colombia",
        "telefono": "6027778888",
        "usuario_actualizacion": "admin@system.com"
    }
    
    print(f"PATCH /vendedores/{vendedor_id}")
    print("Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    response = requests.patch(f"{BASE_URL}/vendedores/{vendedor_id}", json=payload)
    print_response(response)

def test_listar_vendedores():
    """Test 9: Listar vendedores con paginación."""
    print_section("TEST 9: Listar vendedores")
    
    print("GET /vendedores?page=1&size=10")
    print()
    
    response = requests.get(f"{BASE_URL}/vendedores?page=1&size=10")
    print_response(response)

def test_listar_vendedores_filtro_zona():
    """Test 10: Listar vendedores filtrados por zona."""
    print_section("TEST 10: Listar vendedores por zona")
    
    print("GET /vendedores?zona=Bogotá - Colombia")
    print()
    
    response = requests.get(f"{BASE_URL}/vendedores", params={"zona": "Bogotá - Colombia"})
    print_response(response)

def test_health():
    """Test inicial: Verificar que el servicio está corriendo."""
    print_section("TEST INICIAL: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: No se pudo conectar al servicio: {e}")
        print(f"\nAsegúrate de que el microservicio esté corriendo en {BASE_URL}")
        return False

def main():
    """Ejecuta todos los tests."""
    print("\n" + "🚀 " * 40)
    print("  PRUEBAS MANUALES - API DE VENDEDORES")
    print("  HU KAN-83: Registrar vendedor")
    print("🚀 " * 40)
    
    # Verificar que el servicio esté corriendo
    if not test_health():
        return
    
    # Ejecutar tests
    vendedor_id = test_crear_vendedor_exitoso()
    test_crear_vendedor_sin_telefono()
    test_crear_vendedor_correo_invalido()
    test_crear_vendedor_celular_corto()
    test_crear_vendedor_duplicado()
    test_crear_vendedor_campos_faltantes()
    
    if vendedor_id:
        test_obtener_vendedor(vendedor_id)
        test_actualizar_vendedor(vendedor_id)
    
    test_listar_vendedores()
    test_listar_vendedores_filtro_zona()
    
    print_section("🎉 PRUEBAS COMPLETADAS")
    print("Revisa los resultados arriba para verificar que todo funcione correctamente.\n")

if __name__ == "__main__":
    main()
