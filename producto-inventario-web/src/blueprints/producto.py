from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.productos import ProductoServiceError
from src.services.productos import crear_producto_externo

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
