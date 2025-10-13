from flask_jwt_extended import create_access_token
from src.models.user import User

class AuthServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de autenticación."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

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

    if User.find_by_email(email):
        raise AuthServiceError({'error': 'El usuario ya existe'}, 409)

    user = User(
        email=email,
        password=data['password'],
        nombre=data['nombre'].strip(),
        apellido=data['apellido'].strip()
    )
    user.save()

    access_token = create_access_token(identity=str(user.id))

    return {
        'message': 'Usuario creado exitosamente',
        'data': {
            'user': user.to_dict(),
            'access_token': access_token
        }
    }

def login_user(data):
    """
    Lógica de negocio para el login de un usuario.
    """
    if data is None or not data.get('email') or not data.get('password'):
        raise AuthServiceError({'error': 'Email y contraseña son requeridos'}, 400)

    user = User.find_by_email(data['email'].lower().strip())

    if not user or not user.check_password(data['password']):
        raise AuthServiceError({'error': 'Credenciales inválidas'}, 401)

    if not user.is_active:
        raise AuthServiceError({'error': 'Usuario inactivo'}, 401)

    access_token = create_access_token(identity=str(user.id))

    return {
        'message': 'Login exitoso',
        'data': {
            'user': user.to_dict(),
            'access_token': access_token
        }
    }

def validate_user_token(user_id):
    """
    Lógica de negocio para validar un token y el estado del usuario.
    """
    try:
        user = User.find_by_id(int(user_id))
    except (ValueError, TypeError):
        raise AuthServiceError({'valid': False, 'error': 'ID de usuario inválido en el token'}, 401)

    if not user:
        raise AuthServiceError({
            'error': 'Usuario no encontrado',
            'codigo': 'USUARIO_NO_ENCONTRADO'
        }, 401)

    if not user.is_active:
        raise AuthServiceError({
            'error': 'Usuario inactivo',
            'codigo': 'USUARIO_INACTIVO'
        }, 401)

    return {
        'valid': True,
        'user': user.to_dict(),
        'message': 'Token válido'
    }