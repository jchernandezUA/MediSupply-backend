import os
import requests
from flask import current_app

class VendedorServiceError(Exception):
    """Excepción personalizada para errores en la capa de servicio de vendedores."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def crear_vendedor_externo(datos_vendedor):
    """
    Lógica de negocio para crear un vendedor a través del microservicio externo.

    Args:
        datos_vendedor (dict): Datos del vendedor a crear.

    Returns:
        dict: Los datos del vendedor creado.

    Raises:
        VendedorServiceError: Si ocurre un error de validación, conexión o del microservicio.
    """
    if not datos_vendedor:
        raise VendedorServiceError({'error': 'No se proporcionaron datos'}, 400)

    # --- Validación de datos de entrada ---
    required_fields = ['identificacion', 'nombre', 'zona', 'estado']
    missing_fields = [field for field in required_fields if not datos_vendedor.get(field)]
    if missing_fields:
        raise VendedorServiceError({'error': f"Campos faltantes: {', '.join(missing_fields)}"}, 400)

    # --- Fin de la validación ---

    vendedores_url = os.environ.get('VENDEDORES_URL', 'http://localhost:5007/v1')

    try:
        response = requests.post(
            f"{vendedores_url}/vendedores",
            json=datos_vendedor,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()  # Lanza HTTPError para respuestas 4xx/5xx

        datos_respuesta = response.json()
        return datos_respuesta
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Error del microservicio de vendedores: {e.response.text}")
        raise VendedorServiceError(e.response.json(), e.response.status_code)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error de conexión con microservicio de vendedores: {str(e)}")
        raise VendedorServiceError({
            'error': 'Error de conexión con el microservicio de vendedores',
            'codigo': 'ERROR_CONEXION'
        }, 503)
