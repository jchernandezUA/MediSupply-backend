from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import os

# Crear el blueprint para proveedores
proveedor_bp = Blueprint('proveedor', __name__)

@proveedor_bp.route('/proveedor', methods=['POST'])
@jwt_required()
def crear_proveedor():
    """
    BFF endpoint para crear un proveedor
    Requiere autenticación JWT válida
    Se conecta al microservicio de proveedores y retorna la respuesta
    """
    try:
        # Obtener información del usuario autenticado
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Usuario autenticado: {current_user_id}")
        
        # Obtener la URL del microservicio de proveedores desde configuración
        proveedores_url = os.environ.get('PROVEEDORES_URL', 'http://localhost:5002')
        
        # Obtener los datos del request
        datos_proveedor = request.get_json()
        
        if not datos_proveedor:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        # Hacer la llamada al microservicio de proveedores
        response = requests.post(
            f"{proveedores_url}/proveedor",
            json=datos_proveedor,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        # Si el microservicio responde con 201, retornar 201 con los datos
        if response.status_code == 201:
            datos_respuesta = response.json()
            # Agregar información del usuario que creó el proveedor
            datos_respuesta['created_by_user_id'] = current_user_id
            return jsonify(datos_respuesta), 201
        
        # Si hay error, retornar el error del microservicio
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error conectando con microservicio de proveedores: {str(e)}")
        return jsonify({
            'error': 'Error de conexión con el microservicio de proveedores',
            'message': str(e)
        }), 503
    
    except Exception as e:
        current_app.logger.error(f"Error inesperado: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500
