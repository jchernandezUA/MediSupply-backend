from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.proveedores import crear_proveedor_externo, ProveedorServiceError, consultar_proveedores_externo

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
        
         # Obtener datos del formulario
        data = request.form
        files = request.files
        
        # Crear proveedor usando el servicio
        nuevo_proveedor = crear_proveedor_externo(data, files, get_jwt_identity())
        
        return jsonify({
            "data": nuevo_proveedor
        }), 201



    except ProveedorServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        print(e)
        return jsonify(e.message), e.status_code

    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado en el blueprint de proveedor: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': str(object=e)
        }), 500

@proveedor_bp.route('/proveedor', methods=['GET'])
def consultar_proveedores():
    try:
        proveedores = consultar_proveedores_externo()
        return jsonify(proveedores), 200
    except ProveedorServiceError as e:
        # Retornar contenido y código del error personalizado
        return jsonify(e.message), e.status_code
    except Exception:
        # Retornar error genérico como JSON con status 500
        return jsonify({'error': 'Error interno del servidor'}), 500
