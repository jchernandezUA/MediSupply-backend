import pytest
from unittest.mock import patch, Mock, MagicMock
from flask import Flask
import requests
from src.services.proveedores import crear_proveedor_externo, ProveedorServiceError

# Datos válidos para reutilizar
datos_validos = {
    'nombre': 'Proveedor S.A.',
    'nit': '900123456-7',
    'pais': 'Colombia',
    'direccion': 'Calle 123',
    'nombre_contacto': 'Juan Perez',
    'email': 'juan.perez@proveedor.com',
    'telefono': '+573001234567'
}

@pytest.fixture
def app():
    app = Flask(__name__)
    with app.app_context():
        yield app

def test_crear_proveedor_externo_sin_datos():
    with pytest.raises(ProveedorServiceError) as excinfo:
        crear_proveedor_externo(None, 'user1')
    assert excinfo.value.status_code == 400

def test_crear_proveedor_externo_campos_faltantes():
    datos = datos_validos.copy()
    del datos['email']
    with pytest.raises(ProveedorServiceError) as excinfo:
        crear_proveedor_externo(datos, 'user1')
    assert 'email' in str(excinfo.value.message)
    assert excinfo.value.status_code == 400

def test_crear_proveedor_externo_email_invalido():
    datos = datos_validos.copy()
    datos['email'] = 'invalidemail'
    with pytest.raises(ProveedorServiceError) as excinfo:
        crear_proveedor_externo(datos, 'user1')
    assert 'email inválido' in str(excinfo.value.message).lower()

def test_crear_proveedor_externo_telefono_invalido():
    datos = datos_validos.copy()
    datos['telefono'] = '12345'
    with pytest.raises(ProveedorServiceError) as excinfo:
        crear_proveedor_externo(datos, 'user1')
    assert 'teléfono inválido' in str(excinfo.value.message).lower()

@patch('src.services.proveedores.requests.post')
def test_crear_proveedor_externo_exito(mock_post, app):
    mock_logger = Mock()
    mock_app = Mock()
    mock_app.logger = mock_logger

    with patch('src.services.proveedores.current_app', mock_app):
        with app.app_context():
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {'id': '123', 'nombre': datos_validos['nombre']}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = crear_proveedor_externo(datos_validos, 'user1')

            assert result['id'] == '123'
            assert result['created_by_user_id'] == 'user1'
            mock_post.assert_called_once()
            mock_response.raise_for_status.assert_called_once()
            mock_logger.error.assert_not_called()

@patch('src.services.proveedores.requests.post')
def test_crear_proveedor_externo_http_error(mock_post, app):
    mock_logger = Mock()
    mock_app = Mock()
    mock_app.logger = mock_logger

    with patch('src.services.proveedores.current_app', mock_app):
        with app.app_context():
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {'error': 'Validation error'}
            mock_response.text = '{"error": "Validation error"}'
            http_error = requests.exceptions.HTTPError(response=mock_response)

            mock_response.raise_for_status.side_effect = http_error
            mock_post.return_value = mock_response

            with pytest.raises(ProveedorServiceError) as excinfo:
                crear_proveedor_externo(datos_validos, 'user1')

            mock_logger.error.assert_called()
            assert excinfo.value.status_code == 400

@patch('src.services.proveedores.requests.post', side_effect=requests.exceptions.RequestException("Timeout"))
def test_crear_proveedor_externo_connection_error(mock_post, app):
    mock_logger = Mock()
    mock_app = Mock()
    mock_app.logger = mock_logger

    with patch('src.services.proveedores.current_app', mock_app):
        with app.app_context():
            with pytest.raises(ProveedorServiceError) as excinfo:
                crear_proveedor_externo(datos_validos, 'user1')

            mock_logger.error.assert_called()
            assert excinfo.value.status_code == 503
