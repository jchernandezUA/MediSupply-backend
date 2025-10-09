import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from unittest.mock import patch

from src.blueprints.auth import auth_bp
from src.services.auth_service import AuthServiceError

@pytest.fixture
def app():
    """Crea una instancia de la aplicación Flask para las pruebas."""
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    JWTManager(app)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    return app

@pytest.fixture
def client(app):
    """Proporciona un cliente de pruebas para la aplicación."""
    return app.test_client()

@pytest.fixture
def access_token(app):
    """Crea un token de acceso de prueba."""
    with app.app_context():
        return create_access_token(identity="user-123")

# --- Pruebas para el endpoint /signup ---

def test_signup_exito(client):
    """Prueba el registro exitoso a través del endpoint."""
    signup_data = {"email": "new@user.com", "password": "password123", "nombre": "New", "apellido": "User"}
    service_response = {"message": "Usuario creado", "access_token": "fake_token"}
    
    with patch('src.blueprints.auth.register_user', return_value=service_response) as mock_service:
        response = client.post('/auth/signup', json=signup_data)
        
        assert response.status_code == 201
        assert response.get_json() == service_response
        mock_service.assert_called_once_with(signup_data)

def test_signup_error_servicio(client):
    """Prueba que el endpoint maneja errores del servicio de registro."""
    error_msg = {'error': 'El usuario ya existe'}
    with patch('src.blueprints.auth.register_user', side_effect=AuthServiceError(error_msg, 409)):
        response = client.post('/auth/signup', json={})
        
        assert response.status_code == 409
        assert response.get_json() == error_msg

def test_signup_error_inesperado(client):
    """Prueba el manejo de un error inesperado en el endpoint de registro."""
    with patch('src.blueprints.auth.register_user', side_effect=Exception("DB down")):
        response = client.post('/auth/signup', json={})

        assert response.status_code == 500
        json_data = response.get_json()
        assert json_data['error'] == 'Error interno del servidor'
        assert json_data['message'] == 'DB down'


# --- Pruebas para el endpoint /login ---

def test_login_exito(client):
    """Prueba el login exitoso a través del endpoint."""
    login_data = {"email": "test@user.com", "password": "password123"}
    service_response = {"message": "Login exitoso", "access_token": "fake_token"}
    
    with patch('src.blueprints.auth.login_user', return_value=service_response) as mock_service:
        response = client.post('/auth/login', json=login_data)
        
        assert response.status_code == 200
        assert response.get_json() == service_response
        mock_service.assert_called_once_with(login_data)

def test_login_error_servicio(client):
    """Prueba que el endpoint maneja errores del servicio de login."""
    error_msg = {'error': 'Credenciales inválidas'}
    with patch('src.blueprints.auth.login_user', side_effect=AuthServiceError(error_msg, 401)):
        response = client.post('/auth/login', json={})
        
        assert response.status_code == 401
        assert response.get_json() == error_msg

def test_login_error_inesperado(client):
    """Prueba el manejo de un error inesperado en el endpoint de login."""
    with patch('src.blueprints.auth.login_user', side_effect=Exception("Cache failed")):
        response = client.post('/auth/login', json={})

        assert response.status_code == 500
        json_data = response.get_json()
        assert json_data['error'] == 'Error interno del servidor'
        assert json_data['message'] == 'Cache failed'


# --- Pruebas para el endpoint /validate ---

def test_validate_token_exito(client, access_token):
    """Prueba la validación exitosa de un token."""
    service_response = {"valid": True, "user": {"id": "user-123"}}
    
    with patch('src.blueprints.auth.validate_user_token', return_value=service_response) as mock_service:
        response = client.post('/auth/validate', headers={"Authorization": f"Bearer {access_token}"})
        
        assert response.status_code == 200
        assert response.get_json() == service_response
        mock_service.assert_called_once_with("user-123")

def test_validate_token_sin_token(client):
    """Prueba que el endpoint de validación está protegido."""
    response = client.post('/auth/validate')
    assert response.status_code == 401

def test_validate_token_error_inesperado(client, access_token):
    """Prueba el manejo de un error inesperado en el endpoint de validación."""
    with patch('src.blueprints.auth.validate_user_token', side_effect=Exception("Something broke")):
        response = client.post('/auth/validate', headers={"Authorization": f"Bearer {access_token}"})

        assert response.status_code == 500
        json_data = response.get_json()
        assert json_data['error'] == 'Error interno del servidor'
        assert json_data['message'] == 'Something broke'