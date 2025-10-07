import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.extensions import db
from app.models.proveedor import Proveedor, Certificacion
from app.services.proveedor_service import ProveedorService
import tempfile
import os

@pytest.fixture
def app():
    """Fixture para crear la aplicación Flask"""
    app = create_app()
    # Usar la configuración específica de testing
    app.config.from_object('app.config.TestingConfig')
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

class TestFileOperations:
    """Tests específicos para operaciones de archivo"""
    
    @pytest.fixture
    def app_with_temp_dir(self):
        """App con directorio temporal real"""
        app = create_app()
        # Usar configuración de testing
        app.config.from_object('app.config.TestingConfig')
        temp_dir = tempfile.mkdtemp()
        app.config['UPLOAD_FOLDER'] = temp_dir
        
        with app.app_context():
            db.create_all()
            yield app, temp_dir
            db.session.remove()
            db.drop_all()
        
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    def test_guardar_certificacion_directorio_creacion(self, app_with_temp_dir):
        """Test que se creen los directorios necesarios"""
        app, temp_dir = app_with_temp_dir
        
        with app.app_context():
            mock_file = MagicMock()
            mock_file.filename = 'test.pdf'
            mock_file.save = MagicMock()
            
            with patch('os.path.getsize', return_value=1024):
                cert = ProveedorService._guardar_certificacion(123, mock_file)
            
            # Verificar que se creó el directorio relativo a la ubicación actual
            expected_dir = os.path.join('uploads', 'certificaciones', '123')
            assert os.path.exists(expected_dir)
    
    def test_guardar_certificacion_nombre_unico(self, app_with_temp_dir):
        """Test que se generen nombres únicos para archivos"""
        app, temp_dir = app_with_temp_dir
        
        with app.app_context():
            mock_file1 = MagicMock()
            mock_file1.filename = 'test.pdf'
            mock_file1.save = MagicMock()
            
            mock_file2 = MagicMock()
            mock_file2.filename = 'test.pdf'  # Mismo nombre
            mock_file2.save = MagicMock()
            
            with patch('os.path.getsize', return_value=1024):
                cert1 = ProveedorService._guardar_certificacion(456, mock_file1)
                cert2 = ProveedorService._guardar_certificacion(456, mock_file2)
            
            # Los archivos deben tener rutas diferentes
            assert cert1.ruta_archivo != cert2.ruta_archivo
            assert 'test.pdf' in cert1.ruta_archivo
            assert 'test.pdf' in cert2.ruta_archivo

class TestErrorScenarios:
    """Tests para escenarios de error específicos"""
    
    @pytest.fixture
    def app_with_db_error(self):
        """App configurada para simular errores de DB"""
        app = create_app()
        # Usar configuración de testing
        app.config.from_object('app.config.TestingConfig')
        app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        
        with app.app_context():
            db.create_all()
            yield app
    
    def test_crear_proveedor_error_flush(self, app_with_db_error):
        """Test error durante flush de base de datos"""
        with app_with_db_error.app_context():
            data = {
                'nombre': 'Test',
                'nit': '1234567890',
                'pais': 'Colombia',
                'direccion': 'Dir',
                'nombre_contacto': 'Contact',
                'email': 'test@test.com',
                'telefono': '123456789'  # Telefono válido
            }
            
            mock_file = MagicMock()
            mock_file.filename = 'test.pdf'
            mock_file.content_length = 1024
            mock_file.seek = MagicMock()
            mock_file.tell = MagicMock(return_value=1024)
            
            # Simular error en flush
            with patch.object(db.session, 'flush', side_effect=Exception("Flush error")):
                with pytest.raises(ValueError) as exc_info:
                    ProveedorService.crear_proveedor(data, [mock_file])
                
                error = exc_info.value.args[0]
                assert 'Error inesperado' in error['error']
    
    def test_crear_proveedor_error_guardar_archivo(self, app_with_db_error):
        """Test error al guardar archivo físico"""
        with app_with_db_error.app_context():
            data = {
                'nombre': 'Test',
                'nit': '1234567890', 
                'pais': 'Colombia',
                'direccion': 'Dir',
                'nombre_contacto': 'Contact',
                'email': 'test@test.com',
                'telefono': '123456789'  # Telefono válido
            }
            
            mock_file = MagicMock()
            mock_file.filename = 'test.pdf'
            mock_file.content_length = 1024
            mock_file.seek = MagicMock()
            mock_file.tell = MagicMock(return_value=1024)
            mock_file.save = MagicMock(side_effect=Exception("Save error"))
            
            with pytest.raises(ValueError) as exc_info:
                ProveedorService.crear_proveedor(data, [mock_file])
            
            error = exc_info.value.args[0]
            assert 'Error inesperado' in error['error']

class TestPerformance:
    """Tests de rendimiento y carga"""
    
    @pytest.mark.slow
    def test_crear_multiples_proveedores(self, app):
        """Test crear múltiples proveedores secuencialmente"""
        with app.app_context():
            import time
            start_time = time.time()
            
            for i in range(10):
                data = {
                    'nombre': f'Proveedor {i}',
                    'nit': f'123456789{i}',
                    'pais': 'Colombia',
                    'direccion': f'Dirección {i}',
                    'nombre_contacto': f'Contacto {i}',
                    'email': f'test{i}@test.com',
                    'telefono': f'12345678{i}'
                }
                
                mock_file = MagicMock()
                mock_file.filename = f'test{i}.pdf'
                mock_file.content_length = 1024
                mock_file.seek = MagicMock()
                mock_file.tell = MagicMock(return_value=1024)
                mock_file.save = MagicMock()
                
                with patch('os.path.getsize', return_value=1024):
                    proveedor = ProveedorService.crear_proveedor(data, [mock_file])
                    assert proveedor.id is not None
            
            end_time = time.time()
            duration = end_time - start_time
            
            # No debería tomar más de 5 segundos crear 10 proveedores
            assert duration < 5.0, f"Creación de 10 proveedores tomó {duration:.2f}s"
    
    def test_validacion_masiva_nits(self):
        """Test validación masiva de NITs"""
        from app.utils.validators import ProveedorValidator
        
        # Generar 1000 NITs para probar
        nits = [f"80012345{i:02d}" for i in range(100)]
        
        import time
        start_time = time.time()
        
        for nit in nits:
            ProveedorValidator.validar_formato_nit(nit)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Validación de 100 NITs no debería tomar más de 1 segundo
        assert duration < 1.0, f"Validación de 100 NITs tomó {duration:.2f}s"

class TestConcurrency:
    """Tests para escenarios de concurrencia simulados"""
    
    def test_crear_proveedor_concurrente_mismo_nit(self, app):
        """Test crear proveedor con mismo NIT concurrentemente (simulado)"""
        with app.app_context():
            data = {
                'nombre': 'Test Concurrent',
                'nit': '9999999999',
                'pais': 'Colombia', 
                'direccion': 'Dir',
                'nombre_contacto': 'Contact',
                'email': 'test@test.com',
                'telefono': '123456789'  # Telefono válido
            }
            
            mock_file = MagicMock()
            mock_file.filename = 'test.pdf'
            mock_file.content_length = 1024
            mock_file.seek = MagicMock()
            mock_file.tell = MagicMock(return_value=1024)
            mock_file.save = MagicMock()
            
            # Primer intento - exitoso
            with patch('os.path.getsize', return_value=1024):
                proveedor1 = ProveedorService.crear_proveedor(data, [mock_file])
                assert proveedor1.nit == data['nit']
            
            # Segundo intento - debe fallar por NIT duplicado
            with patch('os.path.getsize', return_value=1024):
                with pytest.raises(Exception):  # ConflictError o ValueError
                    ProveedorService.crear_proveedor(data, [mock_file])