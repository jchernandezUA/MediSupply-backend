import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.blueprints.vendedores import vendedores_bp
from src.services.vendedores import VendedorServiceError

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    JWTManager(app)
    app.register_blueprint(vendedores_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def access_token(app):
    with app.app_context():
        return create_access_token(identity='user123')

@patch('src.blueprints.vendedores.crear_vendedor_externo')
def test_crear_vendedor_exito(mock_crear_vendedor, client, access_token):
    mock_crear_vendedor.return_value = {'id': 'vendedor1', 'nombre': 'Vendedor Test'}

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/vendedor', json={'nombre': 'Vendedor Test'}, headers=headers)

    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['id'] == 'vendedor1'

@patch('src.blueprints.vendedores.crear_vendedor_externo')
def test_crear_vendedor_error_controlado(mock_crear_vendedor, client, access_token):
    error = VendedorServiceError({'error': 'Error en datos'}, 400)
    mock_crear_vendedor.side_effect = error

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/vendedor', json={'nombre': 'Vendedor Test'}, headers=headers)

    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data

@patch('src.blueprints.vendedores.crear_vendedor_externo')
def test_crear_vendedor_error_inesperado(mock_crear_vendedor, client, access_token, app):
    mock_crear_vendedor.side_effect = Exception('Error inesperado')
    mock_logger = MagicMock()

    with app.app_context():
        with patch('src.blueprints.vendedores.current_app') as mock_current_app:
            mock_current_app.logger = mock_logger

            headers = {'Authorization': f'Bearer {access_token}'}
            response = client.post('/vendedor', json={'nombre': 'Vendedor Test'}, headers=headers)

            assert response.status_code == 500
            json_data = response.get_json()
            assert 'error' in json_data and 'interno' in json_data['error'].lower()
            mock_logger.error.assert_called_once()

def test_crear_vendedor_sin_token(client):
    # Sin autorización debe responder 401
    response = client.post('/vendedor', json={'nombre': 'Vendedor Test'})
    assert response.status_code == 401
