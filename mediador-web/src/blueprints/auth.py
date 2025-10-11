from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.auth import register_user, login_user, AuthServiceError

# Crear el blueprint para autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route(rule='/signup', methods=['POST'])
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