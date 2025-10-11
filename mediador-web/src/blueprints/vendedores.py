from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from src.services.vendedores import crear_vendedor_externo, VendedorServiceError

# Crear el blueprint para vendedores
vendedores_bp = Blueprint('vendedor', __name__)

@vendedores_bp.route('/vendedor', methods=['POST'])
@jwt_required()
def crear_vendedor():
    """
    Endpoint del BFF para crear un vendedor.
    Delega la lógica de negocio al servicio de vendedores.
    """
    try:
        datos_vendedor = request.get_json()
        
        # Llamar a la capa de servicio para manejar la lógica
        datos_respuesta = crear_vendedor_externo(datos_vendedor)
        
        return jsonify(datos_respuesta), 201

    except VendedorServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        return jsonify(e.message), e.status_code

    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado en el blueprint de vendedor: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500
