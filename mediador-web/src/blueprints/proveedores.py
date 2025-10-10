from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.proveedores import crear_proveedor_externo, ProveedorServiceError

# Crear el blueprint para proveedores
proveedor_bp = Blueprint('proveedor', __name__)

@proveedor_bp.route('/proveedor', methods=['POST'])
@jwt_required()
def crear_proveedor():
    """
    Endpoint del BFF para crear un proveedor.
    Delega la lógica de negocio al servicio de proveedores.
    """
    try:
        current_user_id = get_jwt_identity()
        datos_proveedor = request.get_json()
        
        # Llamar a la capa de servicio para manejar la lógica
        datos_respuesta = crear_proveedor_externo(datos_proveedor, current_user_id)
        
        return jsonify(datos_respuesta), 201

    except ProveedorServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        return jsonify(e.message), e.status_code

    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado en el blueprint de proveedor: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500
