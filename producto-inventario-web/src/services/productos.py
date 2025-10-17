import os
import requests
from flask import current_app, jsonify
from src.config.config import Config as config

class ProductoServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de productos."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def crear_producto_externo(datos_producto, files, user_id):
    """
    Lógica de negocio para crear un producto a través del microservicio externo.

    Args:
        datos_producto (dict): Datos del producto a crear.
        user_id (str): ID del usuario que realiza la creación.
        files (list): Archivos asociados al producto.
    Returns:
        dict: Los datos del producto creado.

    Raises:
        VendedorServiceError: Si ocurre un error de validación, conexión o del microservicio.
    """
    if not datos_producto:
        raise ProductoServiceError({
            'error': 'No se proporcionaron datos',
            'codigo': 'DATOS_VACIOS'
        }, 400)

    # --- Validación de datos de entrada ---
    required_fields = [
        'nombre', 
        'codigo_sku', 
        'categoria', 
        'precio_unitario', 
        'condiciones_almacenamiento', 
        'fecha_vencimiento', 
        'proveedor_id'
        ]
    missing_fields = [field for field in required_fields if not datos_producto.get(field)]
    if missing_fields:
        raise ProductoServiceError({
            'error': f"Campos faltantes: {', '.join(missing_fields)}",
            'codigo': 'CAMPOS_FALTANTES'
            },
              400)
    
    data = datos_producto.copy()
    data['usuario_registro'] = user_id


    _files = {}
    if 'certificacion' in files:
        file = files['certificacion']
        _files['certificacion'] = (file.filename, file.stream, file.mimetype)
    else:
        raise ProductoServiceError({'error': 'No se proporcionaron archivos de certificación', 'codigo': 'ARCHIVOS_FALTANTES'}, 400)


    # --- Fin de la validación ---

    url_producto = config.PRODUCTO_URL + '/api/productos'
    response = requests.post(
        url_producto,
        data=data,
        files=_files
    )
    if (response.status_code != 201):
        print(f'SERVICE - Error en el microservicio de productos: {response.text}')
        try:
            error_data = response.json()
        except Exception:
            error_data = {'error': response.text, 'codigo': 'ERROR_INESPERADO'}
        raise ProductoServiceError(error_data, response.status_code)
    datos_respuesta = response.json()
    return datos_respuesta
        

def procesar_producto_batch(file_storage, user_id):
    """
    Procesa un archivo CSV con productos, valida cada fila según las mismas reglas
    que crear_producto_externo y retorna un resumen con errores por fila.

    Args:
        file_storage: objeto FileStorage de Flask (archivo CSV).
        user_id: id del usuario que ejecuta la carga.

    Returns:
        dict: resumen con conteos y detalles de errores.
    """
    import csv
    from io import StringIO, TextIOWrapper
    from datetime import datetime

    if not file_storage:
        raise ProductoServiceError({'error': 'No se proporcionó archivo'}, 400)

    # leer CSV
    try:
        stream = TextIOWrapper(file_storage.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
    except Exception as e:
        current_app.logger.error(f"Error leyendo CSV: {str(e)}")
        raise ProductoServiceError({'error': 'Error leyendo el archivo CSV'}, 400)

    required_fields = [
        'nombre',
        'codigo_sku',
        'precio_unitario',
        'condiciones_almacenamiento',
        'fecha_vencimiento',
        'certificaciones'
    ]

    total = 0
    errors = []
    successful = 0
    skus_seen = set()
    valid_rows = []

    def validate_row(idx, row):
        row_errors = []
        missing = [f for f in required_fields if not (row.get(f) and str(row.get(f)).strip())]
        if missing:
            row_errors.append(f"Campos faltantes: {', '.join(missing)}")

        sku = (row.get('codigo_sku') or '').strip()
        if sku:
            if sku in skus_seen:
                row_errors.append('SKU duplicado en archivo')
            else:
                skus_seen.add(sku)

        precio = (row.get('precio_unitario') or '').strip()
        if precio:
            try:
                float(precio)
            except Exception:
                row_errors.append('Precio inválido')

        fecha = (row.get('fecha_vencimiento') or '').strip()
        if fecha:
            try:
                datetime.fromisoformat(fecha)
            except Exception:
                row_errors.append('Fecha inválida')

        return row_errors

    for idx, row in enumerate(reader, start=1):
        total += 1
        row_errors = validate_row(idx, row)
        if row_errors:
            errors.append({'fila': idx, 'errors': row_errors, 'row': row})
        else:
            successful += 1
            # normalize row: strip values
            normalized = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            valid_rows.append(normalized)

    result = {
        'total': total,
        'successful': successful,
        'failed': len(errors),
        'errors': errors,
        'valid_rows': valid_rows
    }
    return result


def enviar_batch_productos(file_storage, user_id):
    """
    Envía el archivo CSV original al microservicio de productos como multipart/form-data.
    Retorna la respuesta del backend o lanza ProductoServiceError en caso de fallo.
    """
    if not file_storage:
        raise ProductoServiceError({'error': 'No hay archivo para enviar'}, 400)

    url = config.PRODUCTO_URL + '/api/productos/batch'
    headers = {}
    token = os.environ.get('PRODUCTOS_SERVICE_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'

    # prepare file tuple: (filename, stream, content_type)
    content_type = 'text/csv'
    files = {'file': (file_storage.filename, file_storage.stream, content_type)}
    try:
        resp = requests.post(url, files=files, headers=headers, timeout=120)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {'status_code': resp.status_code}
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error enviando archivo al servicio de productos: {str(e)}")
        raise ProductoServiceError({'error': 'Error enviando archivo al servicio de productos'}, 502)



