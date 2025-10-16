import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from src.blueprints.producto import producto_bp
from src.services.productos import ProductoServiceError

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-key'
    jwt = JWTManager(app)
    app.register_blueprint(producto_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def token(app):
    # Genera un access token de prueba (mockea usuario 'test-user')
    with app.test_request_context():
        from flask_jwt_extended import create_access_token
        return create_access_token(identity='test-user')

def test_crear_producto_exitoso(mocker, client, token):
    # Mock la función crear_producto_externo y identity
    mocker.patch('src.blueprints.producto.crear_producto_externo', return_value={'id': 99, 'nombre': 'Prod'})
    mocker.patch('src.blueprints.producto.get_jwt_identity', return_value='test-user')

    resp = client.post('/producto',
        headers={'Authorization': f'Bearer {token}'},
        data={'nombre': 'Prod'})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['data']['id'] == 99

def test_crear_producto_service_error(mocker, client, token):
    error = ProductoServiceError('Error de negocio', status_code=409)
    mocker.patch('src.blueprints.producto.crear_producto_externo', side_effect=error)
    mocker.patch('src.blueprints.producto.get_jwt_identity', return_value='test-user')

    resp = client.post('/producto',
        headers={'Authorization': f'Bearer {token}'},
        data={'nombre': 'Prod'})
    assert resp.status_code == 409
    assert resp.get_json() == 'Error de negocio'

def test_crear_producto_excepcion_no_controlada(mocker, client, token):
    mocker.patch('src.blueprints.producto.crear_producto_externo', side_effect=Exception('Exploto'))
    mocker.patch('src.blueprints.producto.get_jwt_identity', return_value='test-user')

    resp = client.post('/producto',
        headers={'Authorization': f'Bearer {token}'},
        data={'nombre': 'Prod'})
    assert resp.status_code == 500
    data = resp.get_json()
    assert data['codigo'] == 'ERROR_INESPERADO'
