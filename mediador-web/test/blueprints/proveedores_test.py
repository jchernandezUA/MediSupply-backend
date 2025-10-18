import unittest
from unittest.mock import patch
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.blueprints.proveedores import proveedor_bp
from src.services.proveedores import ProveedorServiceError

class CustomServiceError(ProveedorServiceError):
    def __init__(self):
        self.message = {'error': 'Error controlado'}
        self.status_code = 400

class TestProveedorBlueprint(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['JWT_SECRET_KEY'] = 'test-secret'
        self.app.config['JWT_HEADER_NAME'] = 'Authorization'
        self.app.config['JWT_HEADER_TYPE'] = 'Bearer'
        self.app.config['JWT_TOKEN_LOCATION'] = ['headers']
        JWTManager(self.app)

        self.app.register_blueprint(proveedor_bp)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def get_auth_headers(self):
        with self.app.app_context():
            token = create_access_token(identity="testuser")
        return {"Authorization": f"Bearer {token}"}

    @patch('src.blueprints.proveedores.consultar_proveedores_externo')
    def test_consultar_proveedores_success(self, mock_consulta):
        mock_consulta.return_value = {
            "data": [
                {
                    "direccion": "Carrera 15 # 88 - 35, Oficina 301, Bogotá",
                    "email": "contacto.compras@imglobales.com",
                    "estado": "Activo",
                    "estado_certificacion": "vigente",
                    "fecha_registro": "2025-10-17T04:10:14.826178",
                    "id": 1,
                    "nit": "900123412",
                    "nombre": "Insumos Médicos Globales S.A.S.",
                    "nombre_contacto": "Ana Sofía Rodríguez",
                    "pais": "Colombia",
                    "telefono": "573101234567",
                    "total_certificaciones": 1
                }
            ]
        }
        response = self.client.get('/proveedor')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('Insumos Médicos Globales S.A.S.', data['data'][0]['nombre'])

    @patch('src.blueprints.proveedores.consultar_proveedores_externo')
    def test_consultar_proveedores_service_error(self, mock_consulta):
        mock_consulta.side_effect = CustomServiceError()
        response = self.client.get('/proveedor')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['error'], 'Error controlado')

    @patch('src.blueprints.proveedores.consultar_proveedores_externo')
    def test_consultar_proveedores_generic_error(self, mock_consulta):
        mock_consulta.side_effect = Exception('Error inesperado')
        response = self.client.get('/proveedor')
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertEqual(data['error'], 'Error interno del servidor')

    @patch('src.blueprints.proveedores.crear_proveedor_externo')
    def test_crear_proveedor_success(self, mock_crear):
        mock_crear.return_value = {"id": 1, "nombre": "Proveedor Nuevo"}
        data = {
            "nombre": "Proveedor Nuevo",
            "nit": "123456",
            "pais": "Colombia",
            "direccion": "Calle 123",
            "nombre_contacto": "Ana",
            "email": "correo@example.com",
            "telefono": "+573001234567",
        }
        headers = self.get_auth_headers()
        response = self.client.post('/proveedor', data=data, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Proveedor Nuevo', response.data)

    @patch('src.blueprints.proveedores.crear_proveedor_externo')
    def test_crear_proveedor_controlled_error(self, mock_crear):
        mock_crear.side_effect = CustomServiceError()
        headers = self.get_auth_headers()
        response = self.client.post('/proveedor', data={}, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Error controlado', response.data)

    @patch('src.blueprints.proveedores.crear_proveedor_externo')
    def test_crear_proveedor_unexpected_error(self, mock_crear):
        mock_crear.side_effect = Exception('Fallo crítico')
        headers = self.get_auth_headers()
        response = self.client.post('/proveedor', data={}, headers=headers)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Error interno del servidor', response.data)


if __name__ == '__main__':
    unittest.main()
