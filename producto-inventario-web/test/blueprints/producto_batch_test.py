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
    mocker.patch('src.blueprints.producto.procesar_producto_batch', return_value=mock_summary)
    mocker.patch('src.blueprints.producto.enviar_batch_productos', return_value={'sent': 2, 'errors': []})

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
