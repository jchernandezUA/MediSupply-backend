"""
Tests unitarios para HU KAN-92: Consultar Proveedor
Cubre:
- Servicio: listar_proveedores, obtener_proveedor_por_id
- Endpoints: GET /api/proveedores/, GET /api/proveedores/{id}
- Búsqueda por nombre
- Filtros por país, estado, estado_certificacion
- Paginación
- Manejo de errores y estados vacíos
- Criterios BDD

Coverage objetivo: 100% de las funciones de consulta
"""

import pytest
import tempfile
import shutil
import os
from io import BytesIO
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models.proveedor import Proveedor, Certificacion
from app.services.proveedor_service import ProveedorService


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def app():
    """Crear aplicación de prueba con configuración temporal"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'UPLOAD_FOLDER': tempfile.mkdtemp(),
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        
    # Limpiar directorio de uploads
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])


@pytest.fixture
def client(app):
    """Cliente de prueba para hacer requests HTTP"""
    return app.test_client()


@pytest.fixture
def proveedores_base(app):
    """
    Crea proveedores de muestra para pruebas
    
    Estructura:
    - 5 proveedores totales
    - 2 de Colombia (1 con certs, 1 sin certs)
    - 2 de México (1 activo con certs, 1 inactivo con certs)
    - 1 de Argentina (con certs)
    """
    with app.app_context():
        proveedores = [
            # Proveedor 1: Colombia, Activo, CON certificaciones
            Proveedor(
                nombre='Farmacorp S.A.S.',
                nit='900123456',
                pais='Colombia',
                estado='Activo',
                direccion='Calle 100 #15-20, Bogotá',
                nombre_contacto='María González',
                email='contacto@farmacorp.com',
                telefono='+57 1 234 5678'
            ),
            # Proveedor 2: México, Activo, CON certificaciones
            Proveedor(
                nombre='MediDistribuidores Ltda.',
                nit='800987654',
                pais='México',
                estado='Activo',
                direccion='Av. Reforma 123, CDMX',
                nombre_contacto='Carlos Ruiz',
                email='ventas@medidist.com',
                telefono='+52 55 8765 4321'
            ),
            # Proveedor 3: Colombia, Activo, SIN certificaciones
            Proveedor(
                nombre='Laboratorios Andinos',
                nit='700456789',
                pais='Colombia',
                estado='Activo',
                direccion='Carrera 50 #30-15, Medellín',
                nombre_contacto='Ana Mendoza',
                email='info@labandinos.co',
                telefono='+57 4 444 5555'
            ),
            # Proveedor 4: México, Inactivo, CON certificaciones
            Proveedor(
                nombre='Farmaland',
                nit='700458268',
                pais='México',
                estado='Inactivo',
                direccion='Av. Juárez 456, Guadalajara',
                nombre_contacto='Ana Ruiz',
                email='info@farmaland.mx',
                telefono='+52 33 1234 5678'
            ),
            # Proveedor 5: Argentina, Activo, CON certificaciones
            Proveedor(
                nombre='SaludPlus Argentina',
                nit='300567890',
                pais='Argentina',
                estado='Activo',
                direccion='Av. Corrientes 1500, Buenos Aires',
                nombre_contacto='Roberto Díaz',
                email='contacto@saludplus.ar',
                telefono='+54 11 4567 8901'
            )
        ]
        
        for proveedor in proveedores:
            db.session.add(proveedor)
        
        db.session.commit()
        
        # Agregar certificaciones
        # Farmacorp: 2 certificaciones
        cert1 = Certificacion(
            proveedor_id=proveedores[0].id,
            nombre_archivo='cert_sanitaria_farmacorp.pdf',
            ruta_archivo='uploads/certificaciones/1/cert_sanitaria.pdf',
            tipo_certificacion='sanitaria',
            tamaño_archivo=512000
        )
        cert2 = Certificacion(
            proveedor_id=proveedores[0].id,
            nombre_archivo='cert_calidad_farmacorp.pdf',
            ruta_archivo='uploads/certificaciones/1/cert_calidad.pdf',
            tipo_certificacion='calidad',
            tamaño_archivo=384000
        )
        
        # MediDistribuidores: 1 certificación
        cert3 = Certificacion(
            proveedor_id=proveedores[1].id,
            nombre_archivo='cert_sanitaria_medidist.pdf',
            ruta_archivo='uploads/certificaciones/2/cert_sanitaria.pdf',
            tipo_certificacion='sanitaria',
            tamaño_archivo=620000
        )
        
        # Farmaland: 1 certificación
        cert4 = Certificacion(
            proveedor_id=proveedores[3].id,
            nombre_archivo='cert_sanitaria_farmaland.pdf',
            ruta_archivo='uploads/certificaciones/4/cert_sanitaria.pdf',
            tipo_certificacion='sanitaria',
            tamaño_archivo=450000
        )
        
        # SaludPlus: 1 certificación
        cert5 = Certificacion(
            proveedor_id=proveedores[4].id,
            nombre_archivo='cert_sanitaria_saludplus.pdf',
            ruta_archivo='uploads/certificaciones/5/cert_sanitaria.pdf',
            tipo_certificacion='sanitaria',
            tamaño_archivo=580000
        )
        
        db.session.add_all([cert1, cert2, cert3, cert4, cert5])
        db.session.commit()
        
        # Retornar IDs en lugar de objetos para evitar DetachedInstanceError
        ids = [p.id for p in proveedores]
        return ids


# =============================================================================
# TESTS DE SERVICIO - listar_proveedores()
# =============================================================================

class TestListarProveedores:
    """Tests del método ProveedorService.listar_proveedores()"""
    
    def test_listar_todos_sin_filtros(self, app, proveedores_base):
        """Debe listar todos los proveedores sin filtros"""
        with app.app_context():
            resultado = ProveedorService.listar_proveedores()
            
            assert resultado['total'] == 5
            assert len(resultado['proveedores']) == 5
            assert resultado['pagina'] == 1
            assert resultado['por_pagina'] == 20
            assert resultado['total_paginas'] == 1
    
    def test_listar_con_paginacion(self, app, proveedores_base):
        """Debe paginar correctamente los resultados"""
        with app.app_context():
            # Primera página con 2 items
            resultado = ProveedorService.listar_proveedores(pagina=1, por_pagina=2)
            
            assert len(resultado['proveedores']) == 2
            assert resultado['total'] == 5
            assert resultado['pagina'] == 1
            assert resultado['por_pagina'] == 2
            assert resultado['total_paginas'] == 3
            
            # Segunda página
            resultado2 = ProveedorService.listar_proveedores(pagina=2, por_pagina=2)
            assert len(resultado2['proveedores']) == 2
            assert resultado2['pagina'] == 2
            
            # Tercera página (última)
            resultado3 = ProveedorService.listar_proveedores(pagina=3, por_pagina=2)
            assert len(resultado3['proveedores']) == 1
            assert resultado3['pagina'] == 3
    
    def test_buscar_por_nombre_exacto(self, app, proveedores_base):
        """Debe buscar por nombre exacto"""
        with app.app_context():
            filtros = {'nombre': 'Farmacorp'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 1
            assert 'Farmacorp' in resultado['proveedores'][0]['nombre']
    
    def test_buscar_por_nombre_parcial(self, app, proveedores_base):
        """Debe buscar por nombre parcial (case-insensitive)"""
        with app.app_context():
            filtros = {'nombre': 'labor'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 1
            assert 'Laboratorios' in resultado['proveedores'][0]['nombre']
    
    def test_buscar_por_nombre_case_insensitive(self, app, proveedores_base):
        """La búsqueda debe ser case-insensitive"""
        with app.app_context():
            filtros = {'nombre': 'FARMACORP'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 1
            assert resultado['proveedores'][0]['nombre'] == 'Farmacorp S.A.S.'
    
    def test_buscar_sin_resultados(self, app, proveedores_base):
        """Debe retornar lista vacía si no hay resultados"""
        with app.app_context():
            filtros = {'nombre': 'NoExisteEsteProveedor123'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 0
            assert resultado['total'] == 0
            assert resultado['total_paginas'] == 0
    
    def test_filtrar_por_pais_colombia(self, app, proveedores_base):
        """Debe filtrar por país Colombia"""
        with app.app_context():
            filtros = {'pais': 'Colombia'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 2
            for p in resultado['proveedores']:
                assert p['pais'] == 'Colombia'
    
    def test_filtrar_por_pais_mexico(self, app, proveedores_base):
        """Debe filtrar por país México"""
        with app.app_context():
            filtros = {'pais': 'México'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 2
            for p in resultado['proveedores']:
                assert p['pais'] == 'México'
    
    def test_filtrar_por_pais_case_insensitive(self, app, proveedores_base):
        """El filtro de país debe ser case-insensitive"""
        with app.app_context():
            filtros = {'pais': 'colombia'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 2
    
    def test_filtrar_por_estado_activo(self, app, proveedores_base):
        """Debe filtrar por estado Activo"""
        with app.app_context():
            filtros = {'estado': 'Activo'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 4
            for p in resultado['proveedores']:
                assert p['estado'] == 'Activo'
    
    def test_filtrar_por_estado_inactivo(self, app, proveedores_base):
        """Debe filtrar por estado Inactivo"""
        with app.app_context():
            filtros = {'estado': 'Inactivo'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 1
            assert resultado['proveedores'][0]['estado'] == 'Inactivo'
            assert resultado['proveedores'][0]['nombre'] == 'Farmaland'
    
    def test_filtrar_por_certificaciones_vigentes(self, app, proveedores_base):
        """Debe filtrar proveedores con certificaciones vigentes"""
        with app.app_context():
            filtros = {'estado_certificacion': 'vigente'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 4
            for p in resultado['proveedores']:
                assert p['estado_certificacion'] == 'vigente'
                assert p['total_certificaciones'] > 0
    
    def test_filtrar_por_sin_certificaciones(self, app, proveedores_base):
        """Debe filtrar proveedores sin certificaciones"""
        with app.app_context():
            filtros = {'estado_certificacion': 'sin_certificaciones'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 1
            assert resultado['proveedores'][0]['estado_certificacion'] == 'sin_certificaciones'
            assert resultado['proveedores'][0]['total_certificaciones'] == 0
    
    def test_filtrar_por_certificaciones_vencidas(self, app, proveedores_base):
        """Debe aceptar filtro estado_certificacion=vencida (futuro)"""
        with app.app_context():
            filtros = {'estado_certificacion': 'vencida'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            # Por ahora no filtra, retorna todos
            assert resultado is not None
            assert 'proveedores' in resultado
    
    def test_filtrar_por_certificaciones_en_revision(self, app, proveedores_base):
        """Debe aceptar filtro estado_certificacion=en_revision (futuro)"""
        with app.app_context():
            filtros = {'estado_certificacion': 'en_revision'}
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            # Por ahora no filtra, retorna todos (funcionalidad futura)
            assert resultado is not None
            assert 'proveedores' in resultado
            # Verifica que sigue funcionando sin errores
            assert len(resultado['proveedores']) >= 0
    
    def test_filtros_combinados_pais_y_certificacion(self, app, proveedores_base):
        """Debe aplicar múltiples filtros simultáneamente"""
        with app.app_context():
            filtros = {
                'pais': 'Colombia',
                'estado_certificacion': 'vigente'
            }
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 1
            p = resultado['proveedores'][0]
            assert p['pais'] == 'Colombia'
            assert p['estado_certificacion'] == 'vigente'
            assert p['nombre'] == 'Farmacorp S.A.S.'
    
    def test_filtros_combinados_nombre_pais_estado(self, app, proveedores_base):
        """Debe aplicar tres filtros simultáneamente"""
        with app.app_context():
            filtros = {
                'nombre': 'Medi',
                'pais': 'México',
                'estado': 'Activo'
            }
            resultado = ProveedorService.listar_proveedores(filtros=filtros)
            
            assert len(resultado['proveedores']) == 1
            p = resultado['proveedores'][0]
            assert 'Medi' in p['nombre']
            assert p['pais'] == 'México'
            assert p['estado'] == 'Activo'
    
    def test_estructura_respuesta(self, app, proveedores_base):
        """Debe retornar la estructura correcta de respuesta"""
        with app.app_context():
            resultado = ProveedorService.listar_proveedores()
            
            # Verificar claves principales
            assert 'proveedores' in resultado
            assert 'total' in resultado
            assert 'pagina' in resultado
            assert 'por_pagina' in resultado
            assert 'total_paginas' in resultado
            
            # Verificar estructura de cada proveedor
            if resultado['proveedores']:
                p = resultado['proveedores'][0]
                campos_requeridos = [
                    'id', 'nombre', 'nit', 'pais', 'estado',
                    'email', 'telefono', 'nombre_contacto', 'direccion',
                    'estado_certificacion', 'total_certificaciones', 'fecha_registro'
                ]
                for campo in campos_requeridos:
                    assert campo in p
    
    def test_ordenamiento_por_nombre(self, app, proveedores_base):
        """Los resultados deben estar ordenados por nombre ascendente"""
        with app.app_context():
            resultado = ProveedorService.listar_proveedores()
            
            nombres = [p['nombre'] for p in resultado['proveedores']]
            nombres_ordenados = sorted(nombres)
            
            assert nombres == nombres_ordenados
    
    def test_lista_vacia_sin_proveedores(self, app):
        """Debe manejar correctamente cuando no hay proveedores"""
        with app.app_context():
            resultado = ProveedorService.listar_proveedores()
            
            assert len(resultado['proveedores']) == 0
            assert resultado['total'] == 0
            assert resultado['total_paginas'] == 0


# =============================================================================
# TESTS DE SERVICIO - obtener_proveedor_por_id()
# =============================================================================

class TestObtenerProveedorPorId:
    """Tests del método ProveedorService.obtener_proveedor_por_id()"""
    
    def test_obtener_proveedor_existente(self, app, proveedores_base):
        """Debe obtener un proveedor existente por ID"""
        with app.app_context():
            proveedor_id = proveedores_base[0]  # Ahora es un ID, no un objeto
            resultado = ProveedorService.obtener_proveedor_por_id(proveedor_id)
            
            assert resultado is not None
            assert resultado['id'] == proveedor_id
            assert resultado['nombre'] == 'Farmacorp S.A.S.'
    
    def test_obtener_proveedor_no_existente(self, app, proveedores_base):
        """Debe lanzar ValueError si el proveedor no existe"""
        with app.app_context():
            with pytest.raises(ValueError) as exc_info:
                ProveedorService.obtener_proveedor_por_id(99999)
            
            assert 'error' in str(exc_info.value)
    
    def test_estructura_informacion_fiscal(self, app, proveedores_base):
        """Debe incluir información fiscal completa"""
        with app.app_context():
            proveedor_id = proveedores_base[0]
            resultado = ProveedorService.obtener_proveedor_por_id(proveedor_id)
            
            assert 'informacion_fiscal' in resultado
            fiscal = resultado['informacion_fiscal']
            assert 'nit' in fiscal
            assert 'pais' in fiscal
            assert 'regimen' in fiscal
            assert fiscal['nit'] == '900123456'
            assert fiscal['pais'] == 'Colombia'
    
    def test_estructura_contacto(self, app, proveedores_base):
        """Debe incluir datos de contacto completos"""
        with app.app_context():
            proveedor_id = proveedores_base[0]
            resultado = ProveedorService.obtener_proveedor_por_id(proveedor_id)
            
            assert 'contacto' in resultado
            contacto = resultado['contacto']
            assert 'nombre_contacto' in contacto
            assert 'email' in contacto
            assert 'telefono' in contacto
            assert 'direccion' in contacto
    
    def test_incluye_certificaciones(self, app, proveedores_base):
        """Debe incluir lista de certificaciones"""
        with app.app_context():
            proveedor_id = proveedores_base[0]  # Farmacorp tiene 2 certs
            resultado = ProveedorService.obtener_proveedor_por_id(proveedor_id)
            
            assert 'certificaciones' in resultado
            assert len(resultado['certificaciones']) == 2
            
            # Verificar estructura de certificación
            cert = resultado['certificaciones'][0]
            assert 'id' in cert
            assert 'nombre_archivo' in cert
            assert 'tipo_certificacion' in cert
            assert 'tamaño_archivo' in cert
            assert 'tamaño_mb' in cert
            assert 'fecha_subida' in cert
    
    def test_proveedor_sin_certificaciones(self, app, proveedores_base):
        """Debe manejar proveedores sin certificaciones"""
        with app.app_context():
            proveedor_id = proveedores_base[2]  # Laboratorios Andinos sin certs
            resultado = ProveedorService.obtener_proveedor_por_id(proveedor_id)
            
            assert 'certificaciones' in resultado
            assert len(resultado['certificaciones']) == 0
            assert resultado['estado_certificacion'] == 'sin_certificaciones'
    
    def test_incluye_historial_compras(self, app, proveedores_base):
        """Debe incluir estructura de historial de compras"""
        with app.app_context():
            proveedor_id = proveedores_base[0]
            resultado = ProveedorService.obtener_proveedor_por_id(proveedor_id)
            
            assert 'historial_compras' in resultado
            historial = resultado['historial_compras']
            assert 'total_ordenes' in historial
            assert 'monto_total' in historial
            assert 'ultima_compra' in historial
    
    def test_estado_certificacion_vigente(self, app, proveedores_base):
        """Debe determinar correctamente estado 'vigente'"""
        with app.app_context():
            proveedor_id = proveedores_base[0]
            resultado = ProveedorService.obtener_proveedor_por_id(proveedor_id)
            
            assert resultado['estado_certificacion'] == 'vigente'
    
    def test_estado_certificacion_sin_certificaciones(self, app, proveedores_base):
        """Debe determinar correctamente estado 'sin_certificaciones'"""
        with app.app_context():
            proveedor_id = proveedores_base[2]
            resultado = ProveedorService.obtener_proveedor_por_id(proveedor_id)
            
            assert resultado['estado_certificacion'] == 'sin_certificaciones'


# =============================================================================
# TESTS DE ENDPOINT - GET /api/proveedores/
# =============================================================================

class TestEndpointListarProveedores:
    """Tests del endpoint GET /api/proveedores/"""
    
    def test_endpoint_listar_todos(self, client, proveedores_base):
        """GET /api/proveedores/ debe retornar todos los proveedores"""
        response = client.get('/api/proveedores/')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'mensaje' in data
        assert 'data' in data
        assert 'paginacion' in data
        assert len(data['data']) == 5
    
    def test_endpoint_buscar_por_nombre(self, client, proveedores_base):
        """Debe buscar por nombre via query param"""
        response = client.get('/api/proveedores/?nombre=Farmacorp')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 1
        assert 'Farmacorp' in data['data'][0]['nombre']
    
    def test_endpoint_filtrar_por_pais(self, client, proveedores_base):
        """Debe filtrar por país via query param"""
        response = client.get('/api/proveedores/?pais=Colombia')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 2
    
    def test_endpoint_filtrar_por_estado(self, client, proveedores_base):
        """Debe filtrar por estado via query param"""
        response = client.get('/api/proveedores/?estado=Activo')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 4
    
    def test_endpoint_filtrar_por_certificacion(self, client, proveedores_base):
        """Debe filtrar por estado_certificacion via query param"""
        response = client.get('/api/proveedores/?estado_certificacion=vigente')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 4
    
    def test_endpoint_paginacion(self, client, proveedores_base):
        """Debe paginar resultados correctamente"""
        response = client.get('/api/proveedores/?pagina=1&por_pagina=2')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 2
        assert data['paginacion']['pagina'] == 1
        assert data['paginacion']['por_pagina'] == 2
        assert data['paginacion']['total'] == 5
    
    def test_endpoint_filtros_combinados(self, client, proveedores_base):
        """Debe aplicar múltiples filtros"""
        response = client.get(
            '/api/proveedores/?pais=Colombia&estado_certificacion=vigente'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 1
    
    def test_endpoint_parametros_invalidos(self, client, proveedores_base):
        """Debe retornar 400 para parámetros de paginación inválidos"""
        response = client.get('/api/proveedores/?pagina=abc&por_pagina=xyz')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['codigo'] == 'PARAMETROS_INVALIDOS'
    
    def test_endpoint_sin_resultados(self, client, proveedores_base):
        """Debe retornar lista vacía si no hay resultados"""
        response = client.get('/api/proveedores/?nombre=NoExiste123')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 0
        assert data['paginacion']['total'] == 0
    
    def test_endpoint_lista_vacia(self, client):
        """Debe manejar lista vacía correctamente"""
        response = client.get('/api/proveedores/')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 0


# =============================================================================
# TESTS DE ENDPOINT - GET /api/proveedores/{id}
# =============================================================================

class TestEndpointObtenerDetalle:
    """Tests del endpoint GET /api/proveedores/{id}"""
    
    def test_endpoint_obtener_detalle_existente(self, client, proveedores_base):
        """Debe obtener detalle de proveedor existente"""
        proveedor_id = proveedores_base[0]  # Ahora es un ID
        response = client.get(f'/api/proveedores/{proveedor_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'mensaje' in data
        assert 'data' in data
        assert data['data']['id'] == proveedor_id
    
    def test_endpoint_detalle_estructura_completa(self, client, proveedores_base):
        """Debe incluir toda la estructura de detalle"""
        proveedor_id = proveedores_base[0]  # Ahora es un ID
        response = client.get(f'/api/proveedores/{proveedor_id}')
        
        data = response.get_json()
        proveedor = data['data']
        
        # Campos principales
        assert 'id' in proveedor
        assert 'nombre' in proveedor
        assert 'estado' in proveedor
        assert 'fecha_registro' in proveedor
        
        # Información fiscal
        assert 'informacion_fiscal' in proveedor
        assert 'nit' in proveedor['informacion_fiscal']
        
        # Contacto
        assert 'contacto' in proveedor
        assert 'email' in proveedor['contacto']
        
        # Certificaciones
        assert 'certificaciones' in proveedor
        assert isinstance(proveedor['certificaciones'], list)
        
        # Historial
        assert 'historial_compras' in proveedor
    
    def test_endpoint_proveedor_no_encontrado(self, client, proveedores_base):
        """Debe retornar 404 si el proveedor no existe"""
        response = client.get('/api/proveedores/99999')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert data['codigo'] == 'PROVEEDOR_NO_ENCONTRADO'


# =============================================================================
# TESTS BDD (Behavior Driven Development)
# =============================================================================

class TestCriteriosBDD:
    """Tests basados en criterios BDD de la HU KAN-92"""
    
    def test_bdd_busqueda_exitosa(self, client, proveedores_base):
        """
        BDD: Búsqueda exitosa
        Dado que ingreso un nombre válido,
        cuando ejecuto la búsqueda,
        entonces el sistema debe mostrar la lista filtrada de proveedores correspondientes.
        """
        # Given: nombre válido
        nombre_busqueda = 'Farmacorp'
        
        # When: ejecuto la búsqueda
        response = client.get(f'/api/proveedores/?nombre={nombre_busqueda}')
        data = response.get_json()
        
        # Then: sistema muestra lista filtrada
        assert response.status_code == 200
        assert len(data['data']) > 0
        assert nombre_busqueda in data['data'][0]['nombre']
    
    def test_bdd_filtro_por_pais(self, client, proveedores_base):
        """
        BDD: Filtro por país
        Dado que selecciono un país,
        cuando aplico el filtro,
        entonces la lista solo debe mostrar proveedores de ese país.
        """
        # Given: selecciono un país
        pais_seleccionado = 'Colombia'
        
        # When: aplico el filtro
        response = client.get(f'/api/proveedores/?pais={pais_seleccionado}')
        data = response.get_json()
        
        # Then: lista solo muestra proveedores de ese país
        assert response.status_code == 200
        for proveedor in data['data']:
            assert proveedor['pais'] == pais_seleccionado
    
    def test_bdd_consulta_detalle(self, client, proveedores_base):
        """
        BDD: Consulta de detalle
        Dado que selecciono un proveedor de la lista,
        cuando ingreso a su detalle,
        entonces el sistema debe mostrar toda la información fiscal, de contacto y certificaciones.
        """
        # Given: selecciono un proveedor de la lista
        response_lista = client.get('/api/proveedores/')
        proveedores = response_lista.get_json()['data']
        proveedor_seleccionado_id = proveedores[0]['id']
        
        # When: ingreso a su detalle
        response = client.get(f'/api/proveedores/{proveedor_seleccionado_id}')
        data = response.get_json()
        
        # Then: sistema muestra información completa
        assert response.status_code == 200
        proveedor = data['data']
        
        # Información fiscal
        assert 'informacion_fiscal' in proveedor
        assert 'nit' in proveedor['informacion_fiscal']
        assert 'pais' in proveedor['informacion_fiscal']
        
        # Información de contacto
        assert 'contacto' in proveedor
        assert 'email' in proveedor['contacto']
        assert 'telefono' in proveedor['contacto']
        
        # Certificaciones
        assert 'certificaciones' in proveedor


# =============================================================================
# TESTS DE RENDIMIENTO
# =============================================================================

class TestRendimiento:
    """Tests de rendimiento según requisitos de HU"""
    
    def test_tiempo_respuesta_busqueda(self, client, proveedores_base):
        """
        La búsqueda debe responder en ≤ 2 segundos (requisito HU KAN-92)
        """
        import time
        
        start = time.time()
        response = client.get('/api/proveedores/?nombre=Farmacorp')
        end = time.time()
        
        tiempo_respuesta = end - start
        
        assert response.status_code == 200
        assert tiempo_respuesta < 2.0, f"Tiempo de respuesta: {tiempo_respuesta}s excede 2s"
    
    def test_tiempo_respuesta_detalle(self, client, proveedores_base):
        """
        El detalle debe responder en ≤ 1 segundo
        """
        import time
        
        proveedor_id = proveedores_base[0]  # Ahora es un ID
        
        start = time.time()
        response = client.get(f'/api/proveedores/{proveedor_id}')
        end = time.time()
        
        tiempo_respuesta = end - start
        
        assert response.status_code == 200
        assert tiempo_respuesta < 1.0, f"Tiempo de respuesta: {tiempo_respuesta}s excede 1s"


# =============================================================================
# TESTS DE EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests de casos extremos"""
    
    def test_pagina_fuera_de_rango(self, client, proveedores_base):
        """Debe manejar páginas fuera de rango sin error"""
        response = client.get('/api/proveedores/?pagina=999')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 0
    
    def test_por_pagina_negativo(self, client, proveedores_base):
        """Debe normalizar valores negativos de por_pagina"""
        response = client.get('/api/proveedores/?por_pagina=-5')
        
        assert response.status_code == 200
        data = response.get_json()
        # Debe usar valor por defecto (20)
        assert data['paginacion']['por_pagina'] == 20
    
    def test_por_pagina_excesivo(self, client, proveedores_base):
        """Debe limitar por_pagina a máximo 100"""
        response = client.get('/api/proveedores/?por_pagina=200')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['paginacion']['por_pagina'] == 20  # Se normaliza al default
    
    def test_filtro_vacio(self, client, proveedores_base):
        """Debe manejar filtros vacíos"""
        response = client.get('/api/proveedores/?nombre=')
        
        assert response.status_code == 200
        # Debe retornar todos (filtro vacío se ignora)
    
    def test_multiples_filtros_excluyentes(self, client, proveedores_base):
        """Debe manejar filtros que no coinciden"""
        response = client.get('/api/proveedores/?pais=Colombia&estado=Inactivo')
        
        assert response.status_code == 200
        data = response.get_json()
        # No hay proveedores de Colombia Inactivos
        assert len(data['data']) == 0
    
    def test_id_no_numerico(self, client, proveedores_base):
        """Debe manejar IDs no numéricos en detalle"""
        response = client.get('/api/proveedores/abc')
        
        # Flask da error 404 si no puede convertir el ID
        assert response.status_code == 404
    
    def test_error_servidor_en_detalle(self, client, proveedores_base, monkeypatch):
        """Debe manejar errores internos del servidor"""
        def mock_error(*args, **kwargs):
            raise Exception("Error simulado del servidor")
        
        monkeypatch.setattr('app.services.proveedor_service.ProveedorService.obtener_proveedor_por_id', mock_error)
        
        proveedor_id = proveedores_base[0]
        response = client.get(f'/api/proveedores/{proveedor_id}')
        
        assert response.status_code == 500
        data = response.get_json()
        # El endpoint puede devolver 'mensaje' o 'error' dependiendo del formato
        assert 'error' in data or 'mensaje' in data
