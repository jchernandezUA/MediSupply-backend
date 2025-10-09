from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user import User, db
from datetime import datetime

# Crear el blueprint para autenticación
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Endpoint para registrar un nuevo usuario
    """
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['email', 'password', 'nombre', 'apellido']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'El campo {field} es requerido'}), 400
        
        # Validar formato de email
        email = data['email'].lower().strip()
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Formato de email inválido'}), 400
        
        # Validar longitud de contraseña
        if len(data['password']) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        # Verificar si el usuario ya existe
        if User.find_by_email(email):
            return jsonify({'error': 'El usuario ya existe'}), 409
        
        # Crear nuevo usuario
        user = User(
            email=email,
            password=data['password'],
            nombre=data['nombre'].strip(),
            apellido=data['apellido'].strip()
        )
        
        # Guardar en la base de datos
        user.save()
        
        # Crear token JWT (sin expiración)
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Usuario creado exitosamente',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error en signup: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint para iniciar sesión
    """
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email y contraseña son requeridos'}), 400
        
        # Buscar usuario por email
        user = User.find_by_email(data['email'].lower().strip())
        
        # Verificar usuario y contraseña
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        # Verificar si el usuario está activo
        if not user.is_active:
            return jsonify({'error': 'Usuario inactivo'}), 401
        
        # Crear token JWT (sin expiración)
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login exitoso',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error en login: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@auth_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_token():
    """
    Endpoint para validar el token JWT
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(int(current_user_id))
        
        if not user:
            return jsonify({
                'valid': False,
                'error': 'Usuario no encontrado'
            }), 401
        
        if not user.is_active:
            return jsonify({
                'valid': False,
                'error': 'Usuario inactivo'
            }), 401
        
        return jsonify({
            'valid': True,
            'user': user.to_dict(),
            'message': 'Token válido'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error en validate_token: {str(e)}")
        return jsonify({
            'valid': False,
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500