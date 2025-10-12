import unittest
from unittest.mock import patch
from flask import Flask
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

        self.app.register_blueprint(proveedor_bp)
        self.client = self.app.test_client()

    @patch('flask_jwt_extended.view_decorators.verify_jwt_in_request', return_value=None)
    @patch('src.blueprints.proveedores.get_jwt_identity', return_value='user123')
    @patch('src.blueprints.proveedores.crear_proveedor_externo')
    def test_crear_proveedor_success(self, mock_crear_proveedor, mock_get_identity, mock_verify_jwt):
        mock_crear_proveedor.return_value = {'id': 1, 'nombre': 'Proveedor Test'}

        response = self.client.post('/proveedor', data={'key': 'value'})

        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Proveedor Test', response.data)

    @patch('flask_jwt_extended.view_decorators.verify_jwt_in_request', return_value=None)
    @patch('src.blueprints.proveedores.get_jwt_identity', return_value='user123')
    @patch('src.blueprints.proveedores.crear_proveedor_externo')
    def test_crear_proveedor_service_error(self, mock_crear_proveedor, mock_get_identity, mock_verify_jwt):
        mock_crear_proveedor.side_effect = CustomServiceError()

        response = self.client.post('/proveedor', data={'key': 'value'})

        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Error controlado', response.data)

    @patch('flask_jwt_extended.view_decorators.verify_jwt_in_request', return_value=None)
    @patch('src.blueprints.proveedores.get_jwt_identity', return_value='user123')
    @patch('src.blueprints.proveedores.crear_proveedor_externo')
    def test_crear_proveedor_generic_error(self, mock_crear_proveedor, mock_get_identity, mock_verify_jwt):
        mock_crear_proveedor.side_effect = Exception('Unexpected error')

        response = self.client.post('/proveedor', data={'key': 'value'})

        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Error interno del servidor', response.data)

if __name__ == '__main__':
    unittest.main()
