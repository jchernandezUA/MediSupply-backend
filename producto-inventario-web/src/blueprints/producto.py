from flask import Blueprint, request, jsonify, current_app
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.productos import ProductoServiceError
from src.services.productos import crear_producto_externo
from src.services.productos import procesar_producto_batch, enviar_batch_productos, procesar_y_enviar_producto_batch

# Crear el blueprint para producto
producto_bp = Blueprint('producto', __name__)

@producto_bp.route('/producto', methods=['POST'])
@jwt_required()
def crear_producto():
    """
    Endpoint del BFF para crear un producto.
    Delega la lógica de negocio al servicio de productos.
    """
    try:   
        # Obtener datos del formulario
        data = request.form
        files = request.files        
        # Crear producto usando el servicio
        nuevo_producto = crear_producto_externo(data, files, get_jwt_identity())
        
        # Responder con el producto creado
        print(f"BLUEPRINT - Producto creado: {nuevo_producto}")
        return jsonify({
            "data": nuevo_producto
        }), 201

    except ProductoServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        print(f"BLUEPRINT - Error en ProductoServiceError: {e.message}")
        return jsonify(e.message), e.status_code

    except Exception as e:
        print(f"BLUEPRINT - Error inesperado en producto: {str(e)}")
        # Capturar cualquier otro error no esperado
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INESPERADO'
        }), 500


@producto_bp.route('/producto-batch', methods=['POST'])
@jwt_required()
def producto_batch():
    """
    Endpoint para carga masiva de productos desde un CSV.
    - Valida el CSV y devuelve resumen con errores por fila.
    - Envía los productos válidos al microservicio de productos en chunks.
    """
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No se proporcionó archivo', 'codigo': 'NO_FILE'}), 400

        user_id = get_jwt_identity()
        resultado = procesar_y_enviar_producto_batch(file, user_id)
        if resultado.get('ok'):
            return jsonify({'data': resultado.get('payload')}), resultado.get('status', 200)
        else:
            # payload es un string con el mensaje de error o un dict con detalles
            payload = resultado.get('payload')
            if isinstance(payload, dict):
                # si es dict, devolverlo directamente (ya contiene keys error/codigo)
                return jsonify(payload), resultado.get('status', 400)
            else:
                return jsonify({'error': str(payload), 'codigo': 'VALIDACION_ERROR'}), resultado.get('status', 400)

    except ProductoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en producto-batch: {str(e)}")
        return jsonify({'error': 'Error interno', 'codigo': 'ERROR_INESPERADO'}), 500
