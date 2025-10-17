"""
Tests de integración para las rutas de asignaciones
"""
import pytest
import json
from datetime import date


def test_post_asignacion_exitoso(client):
    """Test crear asignación con datos válidos"""
    # Crear vendedor primero
    vendedor_payload = {
        "nombre": "Vendedor",
        "apellidos": "Asignacion",
        "correo": "vendedor.asignacion.route@example.com",
        "celular": "3001234567"
    }
    response = client.post('/v1/vendedores',
                          data=json.dumps(vendedor_payload),
                          content_type='application/json')
    vendedor_id = json.loads(response.data)["id"]
    
    # Crear asignación
    asignacion_payload = {
        "vendedorId": vendedor_id,
        "zona": "Norte",
        "vigenteDesde": "2025-10-01"
    }
    response = client.post('/v1/asignaciones',
                          data=json.dumps(asignacion_payload),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["vendedorId"] == vendedor_id
    assert data["zona"] == "Norte"
    assert data["activa"] is True


def test_get_asignaciones_lista(client):
    """Test listar asignaciones"""
    # Crear vendedor y asignación
    vendedor_payload = {
        "nombre": "Test",
        "apellidos": "Lista",
        "correo": "test.lista.asig@example.com",
        "celular": "3009876543"
    }
    response = client.post('/v1/vendedores',
                          data=json.dumps(vendedor_payload),
                          content_type='application/json')
    vendedor_id = json.loads(response.data)["id"]
    
    asignacion_payload = {
        "vendedorId": vendedor_id,
        "zona": "Sur",
        "vigenteDesde": "2025-10-01"
    }
    client.post('/v1/asignaciones',
               data=json.dumps(asignacion_payload),
               content_type='application/json')
    
    # Listar asignaciones
    response = client.get('/v1/asignaciones')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


def test_patch_asignacion_cerrar(client):
    """Test cerrar una asignación"""
    # Crear vendedor
    vendedor_payload = {
        "nombre": "Cerrar",
        "apellidos": "Asignacion",
        "correo": "cerrar.asignacion@example.com",
        "celular": "3001111111"
    }
    response = client.post('/v1/vendedores',
                          data=json.dumps(vendedor_payload),
                          content_type='application/json')
    vendedor_id = json.loads(response.data)["id"]
    
    # Crear asignación
    asignacion_payload = {
        "vendedorId": vendedor_id,
        "zona": "Centro",
        "vigenteDesde": "2025-10-01"
    }
    response = client.post('/v1/asignaciones',
                          data=json.dumps(asignacion_payload),
                          content_type='application/json')
    asignacion_id = json.loads(response.data)["id"]
    
    # Cerrar asignación
    cerrar_payload = {
        "vigenteHasta": "2025-10-31"
    }
    response = client.patch(f'/v1/asignaciones/{asignacion_id}',
                           data=json.dumps(cerrar_payload),
                           content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["activa"] is False
    assert data["vigenteHasta"] == "2025-10-31"


def test_get_asignaciones_con_filtros(client):
    """Test listar asignaciones con filtros"""
    # Crear vendedor
    vendedor_payload = {
        "nombre": "Filtros",
        "apellidos": "Asignacion",
        "correo": "filtros.asignacion@example.com",
        "celular": "3002222222"
    }
    response = client.post('/v1/vendedores',
                          data=json.dumps(vendedor_payload),
                          content_type='application/json')
    vendedor_id = json.loads(response.data)["id"]
    
    # Crear asignación
    asignacion_payload = {
        "vendedorId": vendedor_id,
        "zona": "Occidente",
        "vigenteDesde": "2025-10-01"
    }
    client.post('/v1/asignaciones',
               data=json.dumps(asignacion_payload),
               content_type='application/json')
    
    # Filtrar por vendedor
    response = client.get(f'/v1/asignaciones?vendedorId={vendedor_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["total"] >= 1
    
    # Filtrar por zona
    response = client.get('/v1/asignaciones?zona=Occidente')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["total"] >= 1
    
    # Filtrar por activas
    response = client.get('/v1/asignaciones?activas=true')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(item["activa"] for item in data["items"])


def test_post_asignacion_sin_campos(client):
    """Test crear asignación sin campos obligatorios"""
    response = client.post('/v1/asignaciones',
                          data=json.dumps({"zona": "Norte"}),
                          content_type='application/json')
    
    assert response.status_code == 400


def test_patch_asignacion_no_existe(client):
    """Test cerrar asignación que no existe"""
    response = client.patch('/v1/asignaciones/id-inexistente',
                           data=json.dumps({"vigenteHasta": "2025-10-31"}),
                           content_type='application/json')
    
    assert response.status_code == 404
