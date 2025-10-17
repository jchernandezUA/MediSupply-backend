from flask import Blueprint, request, jsonify
from app.services.producto_service import ProductoService, ConflictError
from app.services.csv_service import CSVProductoService, CSVImportError
from app.models.producto import Producto
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


@productos_bp.route('/', methods=['GET'])
def listar_productos():
    """
    Endpoint para listar todos los productos
    
    Query Parameters:
        - page: Número de página (default: 1)
        - per_page: Elementos por página (default: 10, max: 100)
        - categoria: Filtrar por categoría
        - estado: Filtrar por estado (Activo/Inactivo)
        - proveedor_id: Filtrar por proveedor
        - buscar: Buscar en nombre o SKU
        
    Returns:
        200: Lista de productos
        400: Parámetros inválidos
        500: Error interno
    """
    try:
        # Obtener parámetros de consulta
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        categoria = request.args.get('categoria')
        estado = request.args.get('estado')
        proveedor_id = request.args.get('proveedor_id')
        buscar = request.args.get('buscar')
        
        # Construir query base
        query = Producto.query
        
        # Aplicar filtros
        if categoria:
            query = query.filter(Producto.categoria == categoria)
        
        if estado:
            query = query.filter(Producto.estado == estado)
            
        if proveedor_id:
            query = query.filter(Producto.proveedor_id == int(proveedor_id))
            
        if buscar:
            search_pattern = f"%{buscar}%"
            query = query.filter(
                (Producto.nombre.ilike(search_pattern)) | 
                (Producto.codigo_sku.ilike(search_pattern))
            )
        
        # Ordenar por fecha de registro (más recientes primero)
        query = query.order_by(Producto.fecha_registro.desc())
        
        # Paginar
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Serializar productos
        productos = []
        for producto in pagination.items:
            productos.append({
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
                "tiene_certificacion": producto.certificacion is not None
            })
        
        # Preparar respuesta
        respuesta = {
            "productos": productos,
            "paginacion": {
                "pagina_actual": pagination.page,
                "total_paginas": pagination.pages,
                "total_productos": pagination.total,
                "productos_por_pagina": per_page,
                "tiene_siguiente": pagination.has_next,
                "tiene_anterior": pagination.has_prev
            },
            "filtros_aplicados": {
                "categoria": categoria,
                "estado": estado,
                "proveedor_id": proveedor_id,
                "buscar": buscar
            }
        }
        
        return jsonify(respuesta), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Parámetros de consulta inválidos",
            "codigo": "PARAMETROS_INVALIDOS",
            "detalles": str(e)
        }), 400
        
    except Exception as e:
        print(f"Error al listar productos: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "ERROR_INTERNO"
        }), 500


@productos_bp.route('/<int:producto_id>', methods=['GET'])
def obtener_producto(producto_id):
    """
    Endpoint para obtener un producto específico por ID
    
    Args:
        producto_id: ID del producto
        
    Returns:
        200: Producto encontrado
        404: Producto no encontrado
        500: Error interno
    """
    try:
        producto = Producto.query.get(producto_id)
        
        if not producto:
            return jsonify({
                "error": "Producto no encontrado",
                "codigo": "PRODUCTO_NO_ENCONTRADO",
                "producto_id": producto_id
            }), 404
        
        # Serializar producto completo con certificación
        respuesta = {
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
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        print(f"Error al obtener producto: {str(e)}")
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "ERROR_INTERNO"
        }), 500


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
        
    except RequestEntityTooLarge as e:
        print(e.args[0])
        return jsonify({
            "error": "El archivo excede el tamaño máximo permitido de 5MB",
            "codigo": "ARCHIVO_MUY_GRANDE",
            "tamaño_maximo": "5MB"
        }), 413
        
    except ConflictError as e:
        print(e.args[0])
        return jsonify(e.args[0]), 409
        
    except ValueError as e:
        print(e.args[0])
        return jsonify(e.args[0]), 400
        
    except Exception as e:
        print(e.args[0])
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


@productos_bp.route('/importar-csv', methods=['POST'])
def importar_productos_csv():
    """
    Endpoint para importar productos de forma masiva desde un archivo CSV
    
    Espera:
        - archivo CSV con columnas: nombre, codigo_sku, categoria, precio_unitario, 
          condiciones_almacenamiento, fecha_vencimiento, proveedor_id
        - (opcional) usuario_registro en form-data
        
    Returns:
        200: Productos importados (puede incluir errores parciales)
        400: Archivo CSV inválido o errores en formato
        500: Error interno
    """
    try:
        # Verificar que se envió un archivo
        if 'archivo' not in request.files:
            return jsonify({
                "error": "No se proporcionó ningún archivo CSV",
                "codigo": "ARCHIVO_FALTANTE",
                "campo_esperado": "archivo"
            }), 400
        
        archivo = request.files['archivo']
        usuario_importacion = request.form.get('usuario_registro', None)
        
        # Importar productos desde el CSV
        resultados = CSVProductoService.importar_productos_csv(archivo, usuario_importacion)
        
        # Determinar código de estado según resultados
        status_code = 200
        if resultados['exitosos'] == 0 and resultados['fallidos'] > 0:
            status_code = 400
        
        respuesta = {
            "mensaje": "Importación de productos finalizada",
            "estado": "completado" if resultados['exitosos'] > 0 else "fallido",
            "resumen": {
                "total_filas": resultados['total_filas'],
                "exitosos": resultados['exitosos'],
                "fallidos": resultados['fallidos']
            },
            "detalles_exitosos": resultados['detalles_exitosos'],
            "detalles_errores": resultados['detalles_errores']
        }
        
        return jsonify(respuesta), status_code
        
    except CSVImportError as e:
        print(f"Error CSV: {e.args[0]}")
        return jsonify(e.args[0]), 400
        
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        db.session.rollback()
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "ERROR_INTERNO",
            "detalles": str(e)
        }), 500
