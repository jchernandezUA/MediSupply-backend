import os
from flask_jwt_extended import create_access_token
import requests

class AuthServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de autenticación."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

AUTH_USUARIO_URL = os.environ.get('AUTH_USUARIO_URL', 'http://localhost:5003')

def register_user(data):
    """
    Lógica de negocio para registrar un nuevo usuario.
    """
    if data is None:
        raise AuthServiceError({'error': 'No se proporcionaron datos'}, 400)

    required_fields = ['email', 'password', 'nombre', 'apellido']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise AuthServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)

    email = data['email'].lower().strip()
    if '@' not in email or '.' not in email:
        raise AuthServiceError({'error': 'Formato de email inválido'}, 400)

    if len(data['password']) < 6:
        raise AuthServiceError({'error': 'La contraseña debe tener al menos 6 caracteres'}, 400)

    response = requests.post(f'{AUTH_USUARIO_URL}/auth/signup', json=data)

    if response.status_code != 201:
        raise AuthServiceError({'error': 'Error al registrar usuario'}, response.status_code)

    return response.json()

def login_user(data):
    """
    Lógica de negocio para el login de un usuario.
    """
    if data is None or not data.get('email') or not data.get('password'):
        raise AuthServiceError({'error': 'Email y contraseña son requeridos'}, 400)
    
    email = data['email'].lower().strip()
    if '@' not in email or '.' not in email:
        raise AuthServiceError({'error': 'Formato de email inválido'}, 400)

    if len(data['password']) < 6:
        raise AuthServiceError({'error': 'La contraseña debe tener al menos 6 caracteres'}, 400)

    response = requests.post(f'{AUTH_USUARIO_URL}/auth/login', json=data)

    return response.json()