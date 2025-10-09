import pytest
from unittest.mock import patch, Mock, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.blueprints.proveedores import proveedor_bp
from src.services.proveedores import ProveedorServiceError

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    JWTManager(app)
    app.register_blueprint(proveedor_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def access_token(app):
    with app.app_context():
        return create_access_token(identity='user123')

@patch('src.blueprints.proveedores.crear_proveedor_externo')
def test_crear_proveedor_exito(mock_crear_proveedor, client, access_token):
    mock_crear_proveedor.return_value = {'id': 'abc', 'nombre': 'Proveedor Test'}

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/proveedor', json={'nombre': 'Proveedor Test'}, headers=headers)

    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['id'] == 'abc'
    assert json_data['nombre'] == 'Proveedor Test'

@patch('src.blueprints.proveedores.crear_proveedor_externo')
def test_crear_proveedor_error_controlado(mock_crear_proveedor, client, access_token):
    mock_crear_proveedor.side_effect = ProveedorServiceError({'error': 'Error de validación'}, 400)

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/proveedor', json={'nombre': 'Proveedor Test'}, headers=headers)

    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data

@patch('src.blueprints.proveedores.crear_proveedor_externo')
def test_crear_proveedor_error_inesperado(mock_crear_proveedor, client, access_token, app):
    mock_crear_proveedor.side_effect = Exception('Error inesperado')
    mock_logger = MagicMock()

    with app.app_context():
        with patch('src.blueprints.proveedores.current_app') as mock_current_app:
            mock_current_app.logger = mock_logger

            headers = {'Authorization': f'Bearer {access_token}'}
            response = client.post('/proveedor', json={'nombre': 'Proveedor Test'}, headers=headers)

            assert response.status_code == 500
            json_data = response.get_json()
            assert 'error' in json_data and 'interno' in json_data['error'].lower()
            mock_logger.error.assert_called_once()
