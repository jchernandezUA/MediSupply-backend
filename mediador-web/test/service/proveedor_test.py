import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from requests.exceptions import HTTPError, RequestException
from flask import Flask
from src.services.proveedores import crear_proveedor_externo, consultar_proveedores_externo, ProveedorServiceError

class TestProveedorService_Validaciones(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.archivos_validos = {
            'certificaciones': MagicMock(
                filename='cert.pdf',
                stream=BytesIO(b'test content'),
                mimetype='application/pdf'
            )
        }

    def tearDown(self):
        self.app_context.pop()

    def test_crear_proveedor_datos_vacios(self):
        with self.assertRaises(ProveedorServiceError) as cm:
            crear_proveedor_externo(None, self.archivos_validos, 'user1')
        self.assertEqual(cm.exception.status_code, 400)

    def test_crear_proveedor_campos_faltantes(self):
        # Usar un diccionario normal con el campo 'nombre' vacío
        datos = {
            'nombre': '',
            'nit': '123',
            'pais': 'Colombia',
            'direccion': 'Calle X',
            'nombre_contacto': 'Contacto',
            'email': 'email@x.com',
            'telefono': '3001234567',
        }
        with self.assertRaises(ProveedorServiceError) as cm:
            crear_proveedor_externo(datos, self.archivos_validos, 'user1')
        self.assertIn('CAMPOS_FALTANTES', cm.exception.message['codigo'])

    def test_crear_proveedor_email_invalido(self):
        datos = {
            'nombre': 'X',
            'nit': '123',
            'pais': 'Colombia',
            'direccion': 'Calle X',
            'nombre_contacto': 'Contacto',
            'email': 'invalido',
            'telefono': '3001234567',
        }
        with self.assertRaises(ProveedorServiceError) as cm:
            crear_proveedor_externo(datos, self.archivos_validos, 'user1')
        self.assertEqual(cm.exception.message['codigo'], 'EMAIL_INVALIDO')

    def test_crear_proveedor_telefono_invalido(self):
        datos = {
            'nombre': 'X',
            'nit': '123',
            'pais': 'Colombia',
            'direccion': 'Calle X',
            'nombre_contacto': 'Contacto',
            'email': 'email@x.com',
            'telefono': '123',  # número de teléfono inválido
        }
        with self.assertRaises(ProveedorServiceError) as cm:
            crear_proveedor_externo(datos, self.archivos_validos, 'user1')
        self.assertEqual(cm.exception.message['codigo'], 'TELEFONO_INVALIDO')

    def test_crear_proveedor_archivos_faltantes(self):
        # Aquí no hace falta Mock, solo datos válidos y archivos vacíos
        datos = {
            'nombre': 'Proveedor X',
            'nit': '123456789',
            'pais': 'Colombia',
            'direccion': 'Calle 123',
            'nombre_contacto': 'Contact X',
            'email': 'contact@proveedor.com',
            'telefono': '3001234567',
        }
        with self.assertRaises(ProveedorServiceError) as cm:
            crear_proveedor_externo(datos, {}, 'user1')
        self.assertEqual(cm.exception.message['codigo'], 'ARCHIVOS_FALTANTES')


class TestProveedorService_Integracion(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.datos_validos = {
            'nombre': 'Proveedor X',
            'nit': '123456789',
            'pais': 'Colombia',
            'direccion': 'Calle 123',
            'nombre_contacto': 'Contact X',
            'email': 'contact@proveedor.com',
            'telefono': '3001234567',
        }

        self.archivos_validos = {
            'certificaciones': MagicMock(
                filename='cert.pdf',
                stream=BytesIO(b'test content'),
                mimetype='application/pdf'
            )
        }

    def tearDown(self):
        self.app_context.pop()

    @patch('src.services.proveedores.requests.post')
    def test_crear_proveedor_exito(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {'id': 1, 'nombre': 'Proveedor X'}
        mock_post.return_value = mock_resp

        resultado = crear_proveedor_externo(self.datos_validos, self.archivos_validos, 'user1')
        self.assertEqual(resultado['id'], 1)
        self.assertEqual(resultado['created_by_user_id'], 'user1')

    @patch('src.services.proveedores.requests.post')
    def test_crear_proveedor_error_http(self, mock_post):
        mock_resp = MagicMock()
        http_error = HTTPError()
        http_error.response = mock_resp
        mock_resp.raise_for_status.side_effect = http_error
        mock_resp.json.return_value = {'error': 'Bad request'}
        mock_resp.status_code = 400
        mock_post.return_value = mock_resp

        with self.assertRaises(ProveedorServiceError) as cm:
            crear_proveedor_externo(self.datos_validos, self.archivos_validos, 'user1')
        self.assertEqual(cm.exception.status_code, 400)

    @patch('src.services.proveedores.requests.post', side_effect=RequestException('Connection error'))
    def test_crear_proveedor_error_conexion(self, mock_post):
        with self.assertRaises(ProveedorServiceError) as cm:
            crear_proveedor_externo(self.datos_validos, self.archivos_validos, 'user1')
        self.assertEqual(cm.exception.status_code, 503)
        self.assertIn('Error de conexión', cm.exception.message['error'])

    @patch('src.services.proveedores.requests.get')
    def test_consultar_proveedores_exito(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {'data': [{'id': 1, 'nombre': 'Proveedor X'}]}
        mock_get.return_value = mock_resp

        resultado = consultar_proveedores_externo()
        self.assertIn('data', resultado)
        self.assertEqual(resultado['data'][0]['nombre'], 'Proveedor X')

    @patch('src.services.proveedores.requests.get')
    def test_consultar_proveedores_error(self, mock_get):
        mock_get.side_effect = RequestException('Fallo conexión')
        with self.assertRaises(ProveedorServiceError) as cm:
            consultar_proveedores_externo()
        self.assertEqual(cm.exception.status_code, 500)
        self.assertIn('No se pudo consultar', cm.exception.message['error'])

if __name__ == '__main__':
    unittest.main()
