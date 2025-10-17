from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.productos import ProductoServiceError
from src.services.productos import crear_producto_externo
from src.services.productos import procesar_producto_batch, enviar_batch_productos

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
        resumen = procesar_producto_batch(file, user_id)

        # si hay productos válidos, enviarlos al microservicio de productos
        if resumen.get('successful', 0) > 0:
            # rewind file stream and enviar el archivo original
            try:
                file.stream.seek(0)
            except Exception:
                pass
            envio_result = enviar_batch_productos(file, user_id)
            resumen['envio'] = envio_result

        return jsonify({'data': resumen}), 200

    except ProductoServiceError as e:
        return jsonify(e.message), e.status_code
    except Exception as e:
        current_app.logger.error(f"Error en producto-batch: {str(e)}")
        return jsonify({'error': 'Error interno', 'codigo': 'ERROR_INESPERADO'}), 500
