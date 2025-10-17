"""
Tests de integración para las rutas de planes
"""
import pytest
import json


def test_post_plan_exitoso(client):
    """Test crear plan con datos válidos"""
    # Primero crear un vendedor
    vendedor_payload = {
        "nombre": "Vendedor",
        "apellidos": "Planes",
        "correo": "vendedor.planes.route@example.com",
        "celular": "3001234567"
    }
    response = client.post('/v1/vendedores',
                          data=json.dumps(vendedor_payload),
                          content_type='application/json')
    vendedor_id = json.loads(response.data)["id"]
    
    # Crear plan
    plan_payload = {
        "vendedorId": vendedor_id,
        "periodo": "2025-10",
        "objetivoMensual": 5000000
    }
    response = client.post('/v1/planes',
                          data=json.dumps(plan_payload),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["vendedorId"] == vendedor_id
    assert data["periodo"] == "2025-10"
    assert data["objetivoMensual"] == 5000000


def test_get_planes_lista(client):
    """Test listar planes"""
    # Crear vendedor y plan
    vendedor_payload = {
        "nombre": "Test",
        "apellidos": "Lista",
        "correo": "test.lista.planes@example.com",
        "celular": "3009876543"
    }
    response = client.post('/v1/vendedores',
                          data=json.dumps(vendedor_payload),
                          content_type='application/json')
    vendedor_id = json.loads(response.data)["id"]
    
    plan_payload = {
        "vendedorId": vendedor_id,
        "periodo": "2025-11",
        "objetivoMensual": 3000000
    }
    client.post('/v1/planes',
               data=json.dumps(plan_payload),
               content_type='application/json')
    
    # Listar planes
    response = client.get('/v1/planes')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


def test_get_planes_con_filtro_vendedor(client):
    """Test listar planes filtrados por vendedor"""
    # Crear vendedor y plan
    vendedor_payload = {
        "nombre": "Filtro",
        "apellidos": "Vendedor",
        "correo": "filtro.vendedor@example.com",
        "celular": "3001111111"
    }
    response = client.post('/v1/vendedores',
                          data=json.dumps(vendedor_payload),
                          content_type='application/json')
    vendedor_id = json.loads(response.data)["id"]
    
    plan_payload = {
        "vendedorId": vendedor_id,
        "periodo": "2025-12",
        "objetivoMensual": 4000000
    }
    client.post('/v1/planes',
               data=json.dumps(plan_payload),
               content_type='application/json')
    
    # Filtrar por vendedor
    response = client.get(f'/v1/planes?vendedorId={vendedor_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["total"] >= 1
    assert all(item["vendedorId"] == vendedor_id for item in data["items"])


def test_post_plan_sin_campos(client):
    """Test crear plan sin campos obligatorios"""
    response = client.post('/v1/planes',
                          data=json.dumps({"periodo": "2025-10"}),
                          content_type='application/json')
    
    assert response.status_code == 400


def test_post_plan_vendedor_no_existe(client):
    """Test crear plan con vendedor inexistente"""
    plan_payload = {
        "vendedorId": "vendedor-inexistente",
        "periodo": "2025-10",
        "objetivoMensual": 1000000
    }
    response = client.post('/v1/planes',
                          data=json.dumps(plan_payload),
                          content_type='application/json')
    
    assert response.status_code == 404
