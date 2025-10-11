import pytest
from unittest.mock import patch, MagicMock
import requests
from src.services.vendedores import crear_vendedor_externo, VendedorServiceError
from flask import Flask

valid_vendedor_data = {
    'identificacion': '123456789',
    'nombre': 'Juan Perez',
    'zona': 'Norte',
    'estado': 'Activo'
}

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

@pytest.fixture(autouse=True)
def provide_app_context(app):
    with app.app_context():
        yield

@patch('src.services.vendedores.requests.post')
def test_crear_vendedor_externo_exito(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'id': 'vendedor1', 'nombre': 'Juan Perez'}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = crear_vendedor_externo(valid_vendedor_data)
    assert result['nombre'] == 'Juan Perez'
    mock_post.assert_called_once_with(
        'http://localhost:8001/v1/vendedores',
        json=valid_vendedor_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )

def test_crear_vendedor_externo_sin_datos():
    with pytest.raises(VendedorServiceError) as excinfo:
        crear_vendedor_externo(None)
    assert excinfo.value.status_code == 400

def test_crear_vendedor_externo_campos_faltantes():
    data = valid_vendedor_data.copy()
    del data['zona']
    with pytest.raises(VendedorServiceError) as excinfo:
        crear_vendedor_externo(data)
    assert excinfo.value.status_code == 400
    assert 'zona' in str(excinfo.value.message).lower()

@patch('src.services.vendedores.requests.post')
def test_crear_vendedor_externo_http_error(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {'error': 'Datos inválidos'}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_post.return_value = mock_response

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(VendedorServiceError) as excinfo:
            crear_vendedor_externo(valid_vendedor_data)

        mock_logger.error.assert_called_once()
        assert excinfo.value.status_code == 400
        assert 'error' in excinfo.value.message

@patch('src.services.vendedores.requests.post')
def test_crear_vendedor_externo_connection_error(mock_post):
    mock_post.side_effect = requests.exceptions.ConnectionError('Connection failed')

    with patch('src.services.vendedores.current_app') as mock_current_app:
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger

        with pytest.raises(VendedorServiceError) as excinfo:
            crear_vendedor_externo(valid_vendedor_data)

        mock_logger.error.assert_called_once()
        assert excinfo.value.status_code == 503
        assert 'error de conexión' in excinfo.value.message.get('error').lower()
