"""
Tests de integración para las rutas de vendedores
"""
import pytest
import json


def test_post_vendedor_exitoso(client):
    """Test crear vendedor con datos válidos"""
    payload = {
        "nombre": "Juan",
        "apellidos": "Pérez",
        "correo": "juan.perez.route@example.com",
        "telefono": "3001234567"
    }
    
    response = client.post('/v1/vendedores', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert "id" in data
    assert data["nombre"] == "Juan"
    assert data["correo"] == "juan.perez.route@example.com"


def test_post_vendedor_sin_campos(client):
    """Test crear vendedor sin campos obligatorios"""
    response = client.post('/v1/vendedores',
                          data=json.dumps({"nombre": "Test"}),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_post_vendedor_email_invalido(client):
    """Test crear vendedor con email inválido"""
    payload = {
        "nombre": "Test",
        "apellidos": "Test",
        "correo": "email-sin-arroba",
        "telefono": "3001234567"
    }
    
    response = client.post('/v1/vendedores',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 400


def test_get_vendedor_existente(client):
    """Test obtener vendedor por ID"""
    # Crear vendedor primero
    payload = {
        "nombre": "María",
        "apellidos": "García",
        "correo": "maria.garcia.route@example.com",
        "telefono": "3009876543"
    }
    response = client.post('/v1/vendedores',
                          data=json.dumps(payload),
                          content_type='application/json')
    vendedor_id = json.loads(response.data)["id"]
    
    # Obtener vendedor
    response = client.get(f'/v1/vendedores/{vendedor_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["id"] == vendedor_id
    assert data["nombre"] == "María"


def test_get_vendedor_no_existe(client):
    """Test obtener vendedor que no existe"""
    response = client.get('/v1/vendedores/id-inexistente-123')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data


def test_patch_vendedor(client):
    """Test actualizar vendedor"""
    # Crear vendedor
    payload = {
        "nombre": "Pedro",
        "apellidos": "López",
        "correo": "pedro.lopez.route@example.com",
        "telefono": "3001111111"
    }
    response = client.post('/v1/vendedores',
                          data=json.dumps(payload),
                          content_type='application/json')
    vendedor_id = json.loads(response.data)["id"]
    
    # Actualizar vendedor
    update_payload = {"nombre": "Pedro Actualizado", "zona": "Sur"}
    response = client.patch(f'/v1/vendedores/{vendedor_id}',
                           data=json.dumps(update_payload),
                           content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["nombre"] == "Pedro Actualizado"
    assert data["zona"] == "Sur"


def test_get_vendedores_lista(client):
    """Test listar vendedores"""
    # Crear algunos vendedores
    for i in range(3):
        payload = {
            "nombre": f"Vendedor{i}",
            "apellidos": f"Test{i}",
            "correo": f"vendedor{i}.route@example.com",
            "telefono": f"300{i}{i}{i}{i}{i}{i}{i}"
        }
        client.post('/v1/vendedores',
                   data=json.dumps(payload),
                   content_type='application/json')
    
    # Listar vendedores
    response = client.get('/v1/vendedores?page=1&size=10')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert len(data["items"]) >= 3


def test_get_vendedores_con_filtros(client):
    """Test listar vendedores con filtros"""
    # Crear vendedor en zona específica
    payload = {
        "nombre": "Vendedor",
        "apellidos": "Zona",
        "correo": "vendedor.zona.route@example.com",
        "telefono": "3008888888",
        "zona": "Oriente"
    }
    client.post('/v1/vendedores',
               data=json.dumps(payload),
               content_type='application/json')
    
    # Filtrar por zona
    response = client.get('/v1/vendedores?zona=Oriente')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["total"] >= 1


def test_post_vendedor_json_invalido(client):
    """Test crear vendedor con JSON inválido"""
    response = client.post('/v1/vendedores',
                          data='invalid json',
                          content_type='application/json')
    
    # Debería manejar el error gracefully
    assert response.status_code in [400, 500]


def test_patch_vendedor_no_existe(client):
    """Test actualizar vendedor que no existe"""
    response = client.patch('/v1/vendedores/id-inexistente',
                           data=json.dumps({"nombre": "Test"}),
                           content_type='application/json')
    
    assert response.status_code == 404
