import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.services.auth_service import register_user, login_user, validate_user_token, AuthServiceError

@pytest.fixture
def app():
    """Crea una instancia de la aplicación Flask para tener un contexto."""
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    # Necesario para create_access_token
    from flask_jwt_extended import JWTManager
    JWTManager(app)
    return app

# --- Pruebas para register_user ---

def test_register_user_exito(app):
    """Prueba el registro exitoso de un usuario."""
    user_data = {"email": "test@example.com", "password": "password123", "nombre": "Test", "apellido": "User"}
    
    with app.app_context():
        with patch('src.services.auth_service.User') as mock_user_class, \
             patch('src.services.auth_service.create_access_token', return_value="fake_token") as mock_create_token:
            
            # Simular que el usuario no existe
            mock_user_class.find_by_email.return_value = None
            
            # Simular la instancia del usuario y sus métodos
            mock_instance = MagicMock()
            mock_instance.id = 1
            mock_instance.to_dict.return_value = {"id": 1, "email": user_data["email"]}
            mock_user_class.return_value = mock_instance

            result = register_user(user_data)

            mock_user_class.find_by_email.assert_called_once_with(user_data["email"])
            mock_instance.save.assert_called_once()
            mock_create_token.assert_called_once_with(identity="1")
            assert result['access_token'] == "fake_token"
            assert result['user']['email'] == user_data["email"]

@pytest.mark.parametrize("data, expected_error", [
    (None, "No se proporcionaron datos"),
    ({}, "Campos faltantes: email, password, nombre, apellido"),
    ({"email": "a@a.com"}, "Campos faltantes: password, nombre, apellido"),
    ({"email": "invalid", "password": "123", "nombre": "N", "apellido": "A"}, "Formato de email inválido"),
    ({"email": "a@a.com", "password": "123", "nombre": "N", "apellido": "A"}, "La contraseña debe tener al menos 6 caracteres"),
])
def test_register_user_errores_validacion(app, data, expected_error):
    """Prueba varios errores de validación en el registro."""
    with app.app_context():
        with pytest.raises(AuthServiceError) as excinfo:
            register_user(data)
        assert excinfo.value.status_code == 400
        assert expected_error in excinfo.value.message['error']

def test_register_user_ya_existe(app):
    """Prueba el error cuando un usuario ya existe."""
    user_data = {"email": "test@example.com", "password": "password123", "nombre": "Test", "apellido": "User"}
    with app.app_context():
        with patch('src.services.auth_service.User.find_by_email', return_value=MagicMock()):
            with pytest.raises(AuthServiceError) as excinfo:
                register_user(user_data)
            assert excinfo.value.status_code == 409
            assert "El usuario ya existe" in excinfo.value.message['error']

# --- Pruebas para login_user ---

def test_login_user_exito(app):
    """Prueba el login exitoso."""
    login_data = {"email": "test@example.com", "password": "password123"}
    with app.app_context():
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.check_password.return_value = True
        mock_user.to_dict.return_value = {"id": 1, "email": login_data["email"]}

        with patch('src.services.auth_service.User.find_by_email', return_value=mock_user), \
             patch('src.services.auth_service.create_access_token', return_value="fake_token"):
            
            result = login_user(login_data)
            assert result['access_token'] == "fake_token"
            assert result['user']['email'] == login_data["email"]

def test_login_user_credenciales_invalidas(app):
    """Prueba el login con credenciales inválidas (usuario no encontrado o contraseña incorrecta)."""
    with app.app_context():
        # Caso 1: Usuario no encontrado
        with patch('src.services.auth_service.User.find_by_email', return_value=None):
            with pytest.raises(AuthServiceError) as excinfo:
                login_user({"email": "no@existe.com", "password": "123"})
            assert excinfo.value.status_code == 401
            assert "Credenciales inválidas" in excinfo.value.message['error']

        # Caso 2: Contraseña incorrecta
        mock_user = MagicMock()
        mock_user.check_password.return_value = False
        with patch('src.services.auth_service.User.find_by_email', return_value=mock_user):
            with pytest.raises(AuthServiceError) as excinfo:
                login_user({"email": "test@example.com", "password": "wrong"})
            assert excinfo.value.status_code == 401
            assert "Credenciales inválidas" in excinfo.value.message['error']

# --- Pruebas para validate_user_token ---

def test_validate_user_token_exito(app):
    """Prueba la validación exitosa de un token."""
    with app.app_context():
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.to_dict.return_value = {"id": 1, "email": "test@example.com"}
        
        with patch('src.services.auth_service.User.find_by_id', return_value=mock_user):
            result = validate_user_token("1")
            assert result['valid'] is True
            assert result['user']['id'] == 1

def test_validate_user_token_usuario_no_encontrado(app):
    """Prueba la validación cuando el usuario del token no se encuentra."""
    with app.app_context():
        with patch('src.services.auth_service.User.find_by_id', return_value=None):
            with pytest.raises(AuthServiceError) as excinfo:
                validate_user_token("999")
            assert excinfo.value.status_code == 401
            assert "Usuario no encontrado" in excinfo.value.message['error']

def test_validate_user_token_usuario_inactivo(app):
    """Prueba la validación cuando el usuario del token está inactivo."""
    with app.app_context():
        mock_user = MagicMock()
        mock_user.is_active = False
        with patch('src.services.auth_service.User.find_by_id', return_value=mock_user):
            with pytest.raises(AuthServiceError) as excinfo:
                validate_user_token("1")
            assert excinfo.value.status_code == 401
            assert "Usuario inactivo" in excinfo.value.message['error']