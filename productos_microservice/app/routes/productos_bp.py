from flask import Blueprint, request, jsonify
from app.services.producto_service import ProductoService, ConflictError
from app.extensions import db
from datetime import datetime
from werkzeug.exceptions import RequestEntityTooLarge

productos_bp = Blueprint('productos', __name__, url_prefix='/api/productos')


@productos_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "estado": "activo",
        "servicio": "Productos Microservice",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), 200


@productos_bp.route('/', methods=['POST'])
def registrar_producto():
    """
    Endpoint para registrar un nuevo producto
    
    Espera:
        - form-data con campos del producto
        - archivo(s) de certificación
        
    Returns:
        201: Producto creado exitosamente
        400: Datos inválidos
        409: SKU duplicado
        413: Archivo muy grande
        500: Error interno
    """
    try:
        # Obtener datos del formulario
        data = request.form.to_dict()
        
        # Obtener archivo de certificación
        archivos = []
        if 'certificacion' in request.files:
            archivo = request.files['certificacion']
            if archivo.filename:
                archivos.append(archivo)
        
        # Crear producto
        producto = ProductoService.crear_producto(data, archivos)
        
        # Preparar respuesta
        respuesta = {
            "mensaje": "Producto registrado exitosamente",
            "estado": "confirmado",
            "producto": {
                "id": producto.id,
                "nombre": producto.nombre,
                "codigo_sku": producto.codigo_sku,
                "categoria": producto.categoria,
                "precio_unitario": float(producto.precio_unitario),
                "condiciones_almacenamiento": producto.condiciones_almacenamiento,
                "fecha_vencimiento": producto.fecha_vencimiento.strftime("%d/%m/%Y"),
                "estado": producto.estado,
                "proveedor_id": producto.proveedor_id,
                "fecha_registro": producto.fecha_registro.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "usuario_registro": producto.usuario_registro,
                "certificacion": {
                    "id": producto.certificacion.id,
                    "tipo_certificacion": producto.certificacion.tipo_certificacion,
                    "nombre_archivo": producto.certificacion.nombre_archivo,
                    "tamaño_archivo": producto.certificacion.tamaño_archivo,
                    "fecha_subida": producto.certificacion.fecha_subida.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                    "fecha_vencimiento_cert": producto.certificacion.fecha_vencimiento_cert.strftime("%d/%m/%Y")
                } if producto.certificacion else None
            }
        }
        
        return jsonify(respuesta), 201
        
    except RequestEntityTooLarge:
        return jsonify({
            "error": "El archivo excede el tamaño máximo permitido de 5MB",
            "codigo": "ARCHIVO_MUY_GRANDE",
            "tamaño_maximo": "5MB"
        }), 413
        
    except ConflictError as e:
        return jsonify(e.args[0]), 409
        
    except ValueError as e:
        return jsonify(e.args[0]), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "ERROR_INTERNO"
        }), 500


# Manejador de error para archivos muy grandes (413)
@productos_bp.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "error": "El archivo excede el tamaño máximo permitido de 5MB",
        "codigo": "ARCHIVO_MUY_GRANDE",
        "tamaño_maximo": "5MB"
    }), 413
