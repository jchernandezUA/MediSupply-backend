import os
from urllib import response
import requests
from flask import current_app
import re

class ProveedorServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de proveedores."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def _validar_telefono(telefono):
    """Valida que el teléfono tenga el mínimo 7 dígitos."""
    return re.match(r"\d{7,}$", telefono)

def _validar_email(email):
    """Valida que el email tenga un formato básico."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def crear_proveedor_externo(datos_proveedor, files, user_id):
    """
    Lógica de negocio para crear un proveedor a través del microservicio externo.

    Args:
        datos_proveedor (dict): Datos del proveedor a crear.
        user_id (str): ID del usuario que realiza la creación.

    Returns:
        dict: Los datos del proveedor creado y enriquecido.

    Raises:
        ProveedorServiceError: Si ocurre un error de validación, conexión o del microservicio.
    """
    if not datos_proveedor:
        raise ProveedorServiceError({'error': 'No se proporcionaron datos', 'codigo': 'DATOS_VACIOS',}, 400)

    # --- Validación de datos de entrada ---
    required_fields = ['nombre', 'nit', 'pais', 'direccion', 'nombre_contacto', 'email', 'telefono']
    missing_fields = [field for field in required_fields if not datos_proveedor.get(field)]
    if missing_fields:
        raise ProveedorServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}", 'codigo': 'CAMPOS_FALTANTES'}, 400)

    # Validación de formato de email
    if not _validar_email(datos_proveedor['email']):
        raise ProveedorServiceError({'error': 'Formato de email inválido', 'codigo': 'EMAIL_INVALIDO'}, 400)

    # Validación de formato de teléfono
    if not _validar_telefono(datos_proveedor['telefono']):
        raise ProveedorServiceError({'error': 'Formato de teléfono inválido. Debe ser +XX seguido de 10 dígitos (ej: +573001234567).', 'codigo': 'TELEFONO_INVALIDO'}, 400)
    # --- Fin de la validación ---

    _files = {}
    if 'certificaciones' in files:
        file = files['certificaciones']
        _files['certificaciones'] = (file.filename, file.stream, file.mimetype)
    else:
        raise ProveedorServiceError({'error': 'No se proporcionaron archivos de certificación', 'codigo': 'ARCHIVOS_FALTANTES'}, 400)

    proveedores_url = os.environ.get('PROVEEDORES_URL', 'http://localhost:5010/api')

    try:
        response = requests.post(
            f"{proveedores_url}/proveedores",
            data=datos_proveedor.to_dict(),
            files=_files
        )

        response.raise_for_status()  # Lanza HTTPError para respuestas 4xx/5xx

        datos_respuesta = response.json()
        datos_respuesta['created_by_user_id'] = user_id
        return datos_respuesta
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de proveedores: {e.response.text}")
        raise ProveedorServiceError(e.response.json(), e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de proveedores: {str(e)}")
        raise ProveedorServiceError({
            'error': 'Error de conexión con el microservicio de proveedores',
            'codigo': 'ERROR_CONEXION'
        }, 503)