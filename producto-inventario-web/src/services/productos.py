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

    print("Datos del producto a enviar:", datos_producto)


    _files = {}
    if 'certificacion' in files:
        file = files['certificacion']
        _files['certificacion'] = (file.filename, file.stream, file.mimetype)
    else:
        raise ProductoServiceError({'error': 'No se proporcionaron archivos de certificación', 'codigo': 'ARCHIVOS_FALTANTES'}, 400)


    print("Archivos del producto a enviar:", _files)

    # --- Fin de la validación ---
    try:
        url_producto = os.getenv('PRODUCTO_URL', config.PRODUCTO_URL)+'/productos'
        print("Enviando datos al microservicio de productos... "+url_producto)
        response = requests.post(
            url_producto,
            data=data.to_dict(),
            files=_files
        )
        response.raise_for_status()  # Lanza HTTPError para respuestas 4xx/5xx
        datos_respuesta = response.json()
        return datos_respuesta
    except ProductoServiceError as e:
        # Capturar errores controlados desde la capa de servicio
        print(e)
        return jsonify(e.message), e.status_code
    except Exception as e:
        # Capturar cualquier otro error no esperado
        current_app.logger.error(f"Error inesperado en el servicio de producto: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'codigo': 'ERROR_INESPERADO'
        }), 500

