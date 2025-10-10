from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.auth_service import register_user, login_user, validate_user_token, AuthServiceError

# Crear el blueprint para autenticación
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Endpoint para registrar un nuevo usuario
    """
    try:
        data = request.get_json()
        response_data = register_user(data)
        return jsonify(response_data), 201

    except AuthServiceError as e:
        return jsonify(e.message), e.status_code
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
        response_data = login_user(data)
        return jsonify(response_data), 200

    except AuthServiceError as e:
        return jsonify(e.message), e.status_code
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
        response_data = validate_user_token(current_user_id)
        return jsonify(response_data), 200

    except AuthServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en validate_token: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500