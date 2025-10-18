import io
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager

from src.blueprints.producto import producto_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-key'
    jwt = JWTManager(app)
    app.register_blueprint(producto_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def token(app):
    with app.test_request_context():
        from flask_jwt_extended import create_access_token
        return create_access_token(identity='test-user')


def test_producto_batch_no_file(client, token):
    resp = client.post('/producto-batch', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 400
    assert resp.get_json().get('codigo') == 'NO_FILE' or 'No se proporcionó archivo' in resp.get_data(as_text=True)


def test_producto_batch_success(mocker, client, token):
    # Mock procesar_producto_batch to return a summary with valid_rows
    mock_summary = {
        'total': 2,
        'successful': 2,
        'failed': 0,
        'errors': [],
        'valid_rows': [
            {'nombre': 'Prod1', 'codigo_sku': 'SKU1', 'precio_unitario': '10', 'condiciones_almacenamiento': 'A', 'fecha_vencimiento': '2025-12-31', 'certificaciones': ''},
            {'nombre': 'Prod2', 'codigo_sku': 'SKU2', 'precio_unitario': '20', 'condiciones_almacenamiento': 'B', 'fecha_vencimiento': '2025-12-31', 'certificaciones': ''}
        ]
    }
    # ahora la lógica está centralizada en procesar_y_enviar_producto_batch
    mocker.patch('src.blueprints.producto.procesar_y_enviar_producto_batch', return_value={'ok': True, 'status': 200, 'payload': {**mock_summary, 'envio': {'sent': 2, 'errors': []}}})

    data = {
        'file': (io.BytesIO(b'nombre,codigo_sku,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,certificaciones\n'), 'test.csv')
    }

    resp = client.post('/producto-batch', headers={'Authorization': f'Bearer {token}'}, data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert 'data' in body
    resumen = body['data']
    assert resumen['total'] == 2
    assert resumen['successful'] == 2
    assert resumen['envio']['sent'] == 2


def test_producto_batch_error_payload_dict(mocker, client, token):
    # servicio devuelve un payload dict con status personalizado
    mocker.patch('src.blueprints.producto.procesar_y_enviar_producto_batch', return_value={'ok': False, 'status': 422, 'payload': {'error': 'Bad data', 'codigo': 'BAD_DATA'}})
    data = {
        'file': (io.BytesIO(b'nombre,codigo_sku\n'), 'test.csv')
    }
    resp = client.post('/producto-batch', headers={'Authorization': f'Bearer {token}'}, data=data, content_type='multipart/form-data')
    assert resp.status_code == 422
    assert resp.get_json() == {'error': 'Bad data', 'codigo': 'BAD_DATA'}


def test_producto_batch_error_payload_string(mocker, client, token):
    # servicio devuelve un payload string
    mocker.patch('src.blueprints.producto.procesar_y_enviar_producto_batch', return_value={'ok': False, 'status': 400, 'payload': 'Mensaje de validación'})
    data = {
        'file': (io.BytesIO(b'nombre,codigo_sku\n'), 'test.csv')
    }
    resp = client.post('/producto-batch', headers={'Authorization': f'Bearer {token}'}, data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    assert resp.get_json().get('error') == 'Mensaje de validación'


def test_producto_batch_service_error(mocker, client, token):
    # servicio lanza ProductoServiceError
    from src.services.productos import ProductoServiceError
    err = ProductoServiceError({'error': 'servicio caido', 'codigo': 'ERR_SERV'}, 503)
    mocker.patch('src.blueprints.producto.procesar_y_enviar_producto_batch', side_effect=err)
    data = {
        'file': (io.BytesIO(b'nombre,codigo_sku\n'), 'test.csv')
    }
    resp = client.post('/producto-batch', headers={'Authorization': f'Bearer {token}'}, data=data, content_type='multipart/form-data')
    assert resp.status_code == 503
    assert resp.get_json() == {'error': 'servicio caido', 'codigo': 'ERR_SERV'}
