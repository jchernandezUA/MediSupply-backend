import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.blueprints.auth import auth_bp
from src.services.auth import AuthServiceError

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(auth_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_signup_success(client):
    with patch('src.blueprints.auth.register_user') as mock_register_user:
        mock_register_user.return_value = {'id': 'user123', 'email': 'test@example.com'}

        response = client.post('/auth/signup', json={'email': 'test@example.com', 'password': 'pass123', 'nombre': 'Test', 'apellido': 'User'})

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['id'] == 'user123'

def test_signup_auth_service_error(client):
    error = AuthServiceError({'error': 'User exists'}, 409)
    with patch('src.blueprints.auth.register_user', side_effect=error):
        response = client.post('/auth/signup', json={'email': 'test@example.com', 'password': 'pass123', 'nombre': 'Test', 'apellido': 'User'})

        assert response.status_code == 409
        json_data = response.get_json()
        assert 'error' in json_data

def test_signup_unexpected_error(client, app):
    with patch('src.blueprints.auth.register_user', side_effect=Exception('Unexpected error')):
        with app.app_context():
            with patch('src.blueprints.auth.current_app') as mock_current_app:
                mock_logger = MagicMock()
                mock_current_app.logger = mock_logger

                response = client.post('/auth/signup', json={'email': 'test@example.com', 'password': 'pass123', 'nombre': 'Test', 'apellido': 'User'})

                assert response.status_code == 500
                json_data = response.get_json()
                assert 'error' in json_data and 'interno' in json_data['error'].lower()
                mock_logger.error.assert_called_once()

def test_login_success(client):
    with patch('src.blueprints.auth.login_user') as mock_login_user:
        mock_login_user.return_value = {'access_token': 'jwt-token'}

        response = client.post('/auth/login', json={'email': 'test@example.com', 'password': 'pass123'})

        assert response.status_code == 200
        json_data = response.get_json()
        assert 'access_token' in json_data

def test_login_auth_service_error(client):
    error = AuthServiceError({'error': 'Invalid credentials'}, 401)
    with patch('src.blueprints.auth.login_user', side_effect=error):
        response = client.post('/auth/login', json={'email': 'test@example.com', 'password': 'pass123'})

        assert response.status_code == 401
        json_data = response.get_json()
        assert 'error' in json_data

def test_login_unexpected_error(client, app):
    with patch('src.blueprints.auth.login_user', side_effect=Exception('Crash')):
        with app.app_context():
            with patch('src.blueprints.auth.current_app') as mock_current_app:
                mock_logger = MagicMock()
                mock_current_app.logger = mock_logger

                response = client.post('/auth/login', json={'email': 'test@example.com', 'password': 'pass123'})

                assert response.status_code == 500
                json_data = response.get_json()
                assert 'error' in json_data and 'interno' in json_data['error'].lower()
                mock_logger.error.assert_called_once()
