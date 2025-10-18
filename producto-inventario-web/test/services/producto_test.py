import pytest
from werkzeug.datastructures import ImmutableMultiDict
from flask import Flask
from src.services.productos import crear_producto_externo, ProductoServiceError

@pytest.fixture
def fake_config(monkeypatch):
    # Mockea la URL del microservicio
    monkeypatch.setattr('src.services.productos.config', type('C', (), {'PRODUCTO_URL': 'http://fake.url'}))

@pytest.fixture
def fake_requests_post(monkeypatch):
    # Fixture/fake para requests.post que retorna una instancia Response válida
    def _fake(status_code=201, resp_json=None, text="OK"):
        class Response:
            def __init__(self, status_code, resp_json, text):
                self.status_code = status_code
                self._json = resp_json or {"id": 1}
                self.text = text
            def json(self):
                return self._json
        return Response(status_code, resp_json, text)
    return _fake

def build_form_data(valid=True):
    datos = {
        'nombre': 'A',
        'codigo_sku': '111',
        'categoria': 'Bebida',
        'precio_unitario': '10.5',
        'condiciones_almacenamiento': 'Seco',
        'fecha_vencimiento': '2025-10-25',
        'proveedor_id': '42',
    }
    if not valid:
        datos.pop('nombre')
    return ImmutableMultiDict(datos)

def build_files(valid=True):
    if not valid:
        return {}
    class File:
        filename = 'file.pdf'
        stream = b'data'
        mimetype = 'application/pdf'
    return {'certificacion': File()}

def test_raise_if_no_data(fake_config):
    with pytest.raises(ProductoServiceError) as e:
        crear_producto_externo({}, {}, 'user1')
    assert e.value.status_code == 400
    assert e.value.message['codigo'] == 'DATOS_VACIOS'

def test_raise_if_missing_fields(fake_config):
    datos = build_form_data(valid=False)
    with pytest.raises(ProductoServiceError) as e:
        crear_producto_externo(datos, build_files(), 'user1')
    assert e.value.status_code == 400
    assert e.value.message['codigo'] == 'CAMPOS_FALTANTES'

def test_raise_if_missing_files(fake_config):
    datos = build_form_data()
    with pytest.raises(ProductoServiceError) as e:
        crear_producto_externo(datos, {}, 'user1')
    assert e.value.status_code == 400
    assert e.value.message['codigo'] == 'ARCHIVOS_FALTANTES'

def test_ok_returns_json(monkeypatch, fake_config, fake_requests_post):
    datos = build_form_data()
    files = build_files()
    monkeypatch.setattr('src.services.productos.requests.post', lambda *a, **kw: fake_requests_post(status_code=201, resp_json={'ok':'yes'}, text="OK"))
    res = crear_producto_externo(datos, files, 'user1')
    assert res == {'ok':'yes'}

def test_error_microservicio(monkeypatch, fake_config, fake_requests_post):
    datos = build_form_data()
    files = build_files()
    monkeypatch.setattr('src.services.productos.requests.post', lambda *a, **kw: fake_requests_post(status_code=400, resp_json={'error':'fail','codigo':'ERR'}, text="Bad Request"))
    with pytest.raises(ProductoServiceError) as e:
        crear_producto_externo(datos, files, 'u')
    assert e.value.status_code == 400
    assert e.value.message['codigo'] == 'ERR'

def test_error_microservicio_sin_json(monkeypatch, fake_config, fake_requests_post):
    datos = build_form_data()
    files = build_files()
    class R:
        status_code = 500
        text = 'Internal Server Error'
        def json(self): raise Exception()
    monkeypatch.setattr('src.services.productos.requests.post', lambda *a, **kw: R())
    with pytest.raises(ProductoServiceError) as e:
        crear_producto_externo(datos, files, 'u')
    assert e.value.status_code == 500


def test_procesar_batch_date_formats_and_restore_stream():
    from src.services.productos import procesar_producto_batch
    # CSV with different date formats and fecha_vencimiento_cert
    csv = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id,fecha_vencimiento_cert
ProdISO,SKUISO,cat,10.0,Seco,2026-01-01,1,2026-06-01
ProdDMY,SKUDMY,cat,12.0,Seco,15/09/2026,2,15/09/2026
ProdBad,SKUBAD,cat,9.0,Seco,31-02-2026,3,31-02-2026
"""
    f = make_file(csv)
    resumen = procesar_producto_batch(f, 'u')
    # two valid, one invalid
    assert resumen['total'] == 3
    assert resumen['successful'] == 2
    assert resumen['failed'] == 1
    # stream should be restored and readable
    f.stream.seek(0)
    content = f.stream.read()
    assert isinstance(content, (bytes, bytearray))


def test_procesar_y_enviar_producto_batch_success(monkeypatch, fake_config):
    from src.services.productos import procesar_y_enviar_producto_batch
    # create a CSV with a single valid row
    csv = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id
P,SKUX,cat,5.0,Seco,2026-12-31,1
"""
    f = make_file(csv)
    # mock enviar_batch_productos
    monkeypatch.setattr('src.services.productos.enviar_batch_productos', lambda file, user: {'sent': 1})
    res = procesar_y_enviar_producto_batch(f, 'u')
    assert res['ok'] is True
    assert res['status'] == 200
    assert res['payload']['envio']['sent'] == 1


def test_procesar_y_enviar_producto_batch_no_valid():
    from src.services.productos import procesar_y_enviar_producto_batch
    csv = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id
Bad,,cat,abc,Seco,not-a-date,1
"""
    f = make_file(csv)
    res = procesar_y_enviar_producto_batch(f, 'u')
    assert res['ok'] is False
    assert res['status'] == 400
    assert isinstance(res['payload'], str)
    assert 'Nombres inválidos' in res['payload'] or 'Nombres inválidos' in res['payload']


def test_enviar_batch_productos_backend_400(monkeypatch, fake_config):
    from src.services.productos import enviar_batch_productos, ProductoServiceError
    f = make_file('nombre,codigo_sku\nA,1\n')
    class R:
        status_code = 400
        def json(self):
            return {'error': 'bad', 'code': 'ERR'}
        text = 'Bad Request'
    def fake_post(url, files=None, headers=None, timeout=None):
        return R()
    monkeypatch.setattr('src.services.productos.requests.post', fake_post)
    from flask import Flask
    app = Flask(__name__)
    with app.app_context():
        with pytest.raises(ProductoServiceError) as e:
            enviar_batch_productos(f, 'u')
        assert e.value.status_code == 400
        assert isinstance(e.value.message, dict)
        assert 'detail' in e.value.message

def make_file(csv_text, name='test.csv'):
    import io
    class F:
        def __init__(self, b, name):
            self.filename = name
            self.stream = io.BytesIO(b)
            self.mimetype = 'text/csv'
    return F(csv_text.encode('utf-8'), name)


def test_procesar_batch_no_file():
    from src.services.productos import procesar_producto_batch
    with pytest.raises(ProductoServiceError) as e:
        procesar_producto_batch(None, 'u')
    assert e.value.status_code == 400


def test_procesar_batch_missing_fields_and_duplicates():
    from src.services.productos import procesar_producto_batch
    # CSV with missing fields and duplicate SKU and invalid price/date
    csv = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id,certificaciones
Prod1,SKU1,catA,10.5,Seco,2025-12-31,1,cert
Prod2,SKU1,catB,abc,Frio,not-a-date,2,cert
Prod3,,catC,15,Seco,2025-11-30,3,cert
"""
    f = make_file(csv)
    resumen = procesar_producto_batch(f, 'u')
    assert resumen['total'] == 3
    assert resumen['failed'] >= 2
    # ensure errors mention SKU duplicado and Precio inválido and Campos faltantes
    all_errors = ''.join([e['errors'][0] for e in resumen['errors']])
    assert 'SKU duplicado' in all_errors or 'SKU duplicado en archivo' in all_errors
    assert any('Precio inválido' in ''.join(err['errors']) for err in resumen['errors'])
    assert any('Campos faltantes' in ''.join(err['errors']) for err in resumen['errors'])


def test_enviar_batch_productos_success(monkeypatch, fake_config):
    from src.services.productos import enviar_batch_productos
    f = make_file('nombre,codigo_sku\nA,1\n')
    class R:
        status_code = 200
        def json(self):
            return {'ok': True}
        def raise_for_status(self):
            return None
    def fake_post(url, files=None, headers=None, timeout=None):
        assert 'archivo' in files
        return R()
    monkeypatch.setattr('src.services.productos.requests.post', fake_post)
    app = Flask(__name__)
    with app.app_context():
        res = enviar_batch_productos(f, 'u')
    assert res == {'ok': True}


def test_enviar_batch_productos_failure(monkeypatch, fake_config):
    from src.services.productos import enviar_batch_productos
    import requests
    f = make_file('nombre\n')
    def fake_post_fail(*a, **kw):
        raise requests.exceptions.RequestException('fail')
    monkeypatch.setattr('src.services.productos.requests.post', fake_post_fail)
    app = Flask(__name__)
    with app.app_context():
        with pytest.raises(ProductoServiceError) as e:
            enviar_batch_productos(f, 'u')
    assert e.value.status_code == 502
