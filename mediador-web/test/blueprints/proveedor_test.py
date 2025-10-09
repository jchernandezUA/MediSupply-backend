import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from unittest.mock import patch, MagicMock
import requests
from src.blueprints.proveedor import proveedor_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    app.config['TESTING'] = True
    JWTManager(app)
    app.register_blueprint(proveedor_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def access_token(app):
    with app.app_context():
        return create_access_token(identity="123")  # identity como string


def print_response_debug(response):
    print("Status code:", response.status_code)
    print("Response body:", response.get_data(as_text=True))


def test_crear_proveedor_exito(client, access_token):
    datos = {"nombre": "Proveedor 1", "descripcion": "Proveedor prueba"}

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 1, "nombre": "Proveedor 1"}

    with patch('src.blueprints.proveedor.requests.post', return_value=mock_response):
        response = client.post(
            '/proveedor',
            json=datos,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if response.status_code != 201:
            print_response_debug(response)
        assert response.status_code == 201


def test_crear_proveedor_no_data(client, access_token):
    # Ahora enviamos JSON vacío explícito para evitar error 415
    response = client.post(
        '/proveedor',
        json={},  # Enviar JSON vacío válido
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code != 400:
        print_response_debug(response)
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'No se proporcionaron datos'


def test_crear_proveedor_error_microservicio(client, access_token):
    error_response = MagicMock()
    error_response.status_code = 400
    error_response.json.return_value = {"error": "Datos inválidos"}

    with patch('src.blueprints.proveedor.requests.post', return_value=error_response):
        response = client.post(
            '/proveedor',
            json={"nombre": "X"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if response.status_code != 400:
            print_response_debug(response)
        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data['error'] == "Datos inválidos"


def test_crear_proveedor_error_conexion(client, access_token):
    # Ahora la excepción parcheada es requests.exceptions.RequestException para caer en el 503
    with patch('src.blueprints.proveedor.requests.post', side_effect=requests.exceptions.RequestException("Conexion fallida")):
        response = client.post(
            '/proveedor',
            json={"nombre": "X"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if response.status_code != 503:
            print_response_debug(response)
        assert response.status_code == 503
        json_data = response.get_json()
        assert json_data['error'] == 'Error de conexión con el microservicio de proveedores'
        assert "Conexion fallida" in json_data['message']


def test_crear_proveedor_sin_token(client):
    response = client.post(
        '/proveedor',
        json={"nombre": "X"},
    )
    if response.status_code != 401:
        print_response_debug(response)
    assert response.status_code == 401
