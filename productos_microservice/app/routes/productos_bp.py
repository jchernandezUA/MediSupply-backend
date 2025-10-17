from flask import Blueprint, request, jsonify
from app.services.producto_service import ProductoService, ConflictError
from app.services.csv_service import CSVProductoService, CSVImportError
from app.models.producto import Producto
from app.extensions import db
from datetime import datetime
from werkzeug.exceptions import RequestEntityTooLarge
import logging

logger = logging.getLogger(__name__)

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
    Endpoint inteligente para importar productos desde CSV
    
    Decide automáticamente entre procesamiento síncrono o asíncrono:
    - CSV pequeño (< 100 filas): Procesamiento síncrono inmediato
    - CSV grande (≥ 100 filas): Procesamiento asíncrono con SQS
    
    Espera:
        - archivo CSV con columnas requeridas
        - (opcional) usuario_registro en form-data
        - (opcional) forzar_asincrono=true para forzar procesamiento asíncrono
        
    Returns:
        200/202: Según el tipo de procesamiento
        400: Archivo CSV inválido
        500: Error interno
    """
    import io
    import csv
    from app.config.aws_config import AWSConfig
    from app.services.s3_service import S3Service
    from app.services.sqs_service import SQSService
    from app.models.import_job import ImportJob
    
    try:
        # Verificar que se envió un archivo
        if 'archivo' not in request.files:
            return jsonify({
                "error": "No se proporcionó ningún archivo CSV",
                "codigo": "ARCHIVO_FALTANTE",
                "campo_esperado": "archivo"
            }), 400
        
        archivo = request.files['archivo']
        usuario_importacion = request.form.get('usuario_registro', 'sistema')
        forzar_asincrono = request.form.get('forzar_asincrono', 'false').lower() == 'true'
        
        # Validar nombre de archivo
        if not archivo.filename:
            return jsonify({
                "error": "El archivo no tiene nombre",
                "codigo": "ARCHIVO_INVALIDO"
            }), 400
        
        if not archivo.filename.endswith('.csv'):
            return jsonify({
                "error": "El archivo debe ser CSV (.csv)",
                "codigo": "FORMATO_INVALIDO"
            }), 400
        
        # PASO 1: Contar filas rápidamente para decidir procesamiento
        archivo.stream.seek(0)
        contenido = archivo.stream.read().decode('utf-8')
        archivo.stream.seek(0)  # Resetear para uso posterior
        
        # Contar filas
        lineas = contenido.strip().split('\n')
        num_filas = len(lineas) - 1  # -1 por el header
        
        # UMBRAL para decidir procesamiento
        UMBRAL_ASINCRONO = 100
        usar_asincrono = num_filas >= UMBRAL_ASINCRONO or forzar_asincrono
        
        # Verificar si AWS está habilitado para procesamiento asíncrono
        if usar_asincrono and not AWSConfig.USE_AWS:
            return jsonify({
                "error": "Procesamiento asíncrono no disponible (AWS no configurado)",
                "codigo": "AWS_NO_DISPONIBLE",
                "sugerencia": "Configure AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY, o use un CSV más pequeño"
            }), 503
        
        # ============================================
        # PROCESAMIENTO SÍNCRONO (CSV pequeño)
        # ============================================
        if not usar_asincrono:
            logger.info(f"Procesamiento SÍNCRONO: {num_filas} filas")
            
            # Resetear stream
            archivo.stream.seek(0)
            
            # Importar productos inmediatamente
            resultados = CSVProductoService.importar_productos_csv(archivo, usuario_importacion)
            
            # Determinar código de estado
            status_code = 200
            if resultados['exitosos'] == 0 and resultados['fallidos'] > 0:
                status_code = 400
            
            respuesta = {
                "mensaje": "Importación completada",
                "procesamiento": "sincrono",
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
        
        # ============================================
        # PROCESAMIENTO ASÍNCRONO (CSV grande)
        # ============================================
        logger.info(f"Procesamiento ASÍNCRONO: {num_filas} filas")
        
        # 1. Subir archivo a S3
        archivo.stream.seek(0)
        s3_key, nombre_archivo = S3Service.subir_csv(archivo, usuario_importacion)
        
        # 2. Crear job de importación
        job = ImportJob(
            nombre_archivo=nombre_archivo,
            s3_key=s3_key,
            s3_bucket=AWSConfig.S3_BUCKET_CSV,
            estado='PENDIENTE',
            total_filas=num_filas,
            usuario_registro=usuario_importacion,
            metadata={
                'umbral_usado': UMBRAL_ASINCRONO,
                'forzado': forzar_asincrono
            }
        )
        db.session.add(job)
        db.session.commit()
        
        # 3. Enviar mensaje a SQS
        try:
            sqs_response = SQSService.enviar_job_a_cola(
                job_id=job.id,
                s3_key=s3_key,
                nombre_archivo=nombre_archivo,
                usuario_registro=usuario_importacion,
                metadata={'total_filas': num_filas}
            )
            
            # Actualizar job con info de SQS
            job.sqs_message_id = sqs_response['MessageId']
            job.estado = 'EN_COLA'
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error enviando a SQS: {str(e)}")
            job.estado = 'FALLIDO'
            job.mensaje_error = f"Error enviando a cola: {str(e)}"
            db.session.commit()
            
            return jsonify({
                "error": "Error enviando job a cola de procesamiento",
                "codigo": "ERROR_SQS",
                "detalles": str(e),
                "job_id": job.id
            }), 500
        
        # 4. Retornar respuesta asíncrona
        respuesta = {
            "mensaje": "Importación iniciada. El proceso se ejecutará en segundo plano",
            "procesamiento": "asincrono",
            "job_id": job.id,
            "estado": "EN_COLA",
            "nombre_archivo": nombre_archivo,
            "total_filas_estimadas": num_filas,
            "url_status": f"/api/productos/importar-csv/status/{job.id}",
            "sqs_message_id": sqs_response['MessageId'],
            "nota": f"El CSV tiene {num_filas} filas. Se procesará de forma asíncrona."
        }
        
        return jsonify(respuesta), 202  # 202 Accepted
        
    except CSVImportError as e:
        logger.error(f"Error CSV: {e.args[0]}")
        return jsonify(e.args[0]), 400
        
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "ERROR_INTERNO",
            "detalles": str(e)
        }), 500


@productos_bp.route('/importar-csv/status/<job_id>', methods=['GET'])
def obtener_status_importacion(job_id):
    """
    Endpoint para consultar el estado de una importación asíncrona
    
    Args:
        job_id: ID del job de importación
        
    Query Parameters:
        - include_errors: Si incluir detalles de errores (default: false)
        
    Returns:
        200: Estado del job
        404: Job no encontrado
        500: Error interno
    """
    from app.models.import_job import ImportJob
    
    try:
        include_errors = request.args.get('include_errors', 'false').lower() == 'true'
        
        # Buscar job
        job = ImportJob.query.get(job_id)
        
        if not job:
            return jsonify({
                "error": "Job no encontrado",
                "codigo": "JOB_NO_ENCONTRADO",
                "job_id": job_id
            }), 404
        
        # Serializar job
        respuesta = job.to_dict(include_errors=include_errors)
        
        # Agregar información adicional según el estado
        if job.estado == 'EN_COLA':
            respuesta['mensaje'] = "El job está en cola esperando ser procesado"
        elif job.estado == 'PROCESANDO':
            respuesta['mensaje'] = f"Procesando... {respuesta['progreso']}% completado"
        elif job.estado == 'COMPLETADO':
            respuesta['mensaje'] = "Importación completada exitosamente"
        elif job.estado == 'FALLIDO':
            respuesta['mensaje'] = "La importación falló"
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        logger.error(f"Error consultando status del job: {str(e)}")
        return jsonify({
            "error": "Error consultando estado del job",
            "codigo": "ERROR_INTERNO",
            "detalles": str(e)
        }), 500


@productos_bp.route('/importar-csv/jobs', methods=['GET'])
def listar_jobs_importacion():
    """
    Endpoint para listar jobs de importación
    
    Query Parameters:
        - usuario: Filtrar por usuario (opcional)
        - estado: Filtrar por estado (opcional)
        - limit: Límite de resultados (default: 10, max: 100)
        - offset: Offset para paginación (default: 0)
        
    Returns:
        200: Lista de jobs
        500: Error interno
    """
    from app.models.import_job import ImportJob
    
    try:
        # Obtener parámetros
        usuario = request.args.get('usuario')
        estado = request.args.get('estado')
        limit = min(int(request.args.get('limit', 10)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Construir query
        query = ImportJob.query
        
        if usuario:
            query = query.filter(ImportJob.usuario_registro == usuario)
        
        if estado:
            query = query.filter(ImportJob.estado == estado)
        
        # Ordenar por fecha de creación (más recientes primero)
        query = query.order_by(ImportJob.fecha_creacion.desc())
        
        # Contar total
        total = query.count()
        
        # Paginar
        jobs = query.offset(offset).limit(limit).all()
        
        # Serializar
        jobs_data = [job.to_dict(include_errors=False) for job in jobs]
        
        respuesta = {
            "jobs": jobs_data,
            "paginacion": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "tiene_mas": (offset + limit) < total
            },
            "filtros": {
                "usuario": usuario,
                "estado": estado
            }
        }
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        logger.error(f"Error listando jobs: {str(e)}")
        return jsonify({
            "error": "Error listando jobs",
            "codigo": "ERROR_INTERNO",
            "detalles": str(e)
        }), 500
