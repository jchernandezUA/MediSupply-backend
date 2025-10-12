import pytest
import tempfile
import os
from io import BytesIO
from unittest.mock import patch, MagicMock
from app import create_app
from app.extensions import db
from app.models.producto import Producto, CertificacionProducto, CATEGORIAS_VALIDAS
from app.services.producto_service import ProductoService, ConflictError
from app.utils.validators import ProductoValidator, CertificacionValidator
from datetime import datetime

class TestProductoModel:
    """Tests para el modelo Producto"""
    
    def test_producto_creation(self, app):
        """Test creación básica de producto"""
        with app.app_context():
            producto = Producto(
                nombre="Paracetamol 500mg",
                codigo_sku="MED-PARA-500",
                categoria="medicamento",
                precio_unitario=25.50,
                condiciones_almacenamiento="Almacenar en lugar fresco y seco",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="admin@medisupply.com"
            )
            
            # Agregar a sesión para que se apliquen los defaults
            db.session.add(producto)
            db.session.flush()
            
            assert producto.nombre == "Paracetamol 500mg"
            assert producto.codigo_sku == "MED-PARA-500"
            assert producto.estado == "Activo"
            assert producto.esta_activo() == True
    
    def test_producto_activar_desactivar(self, app):
        """Test métodos de activar/desactivar producto"""
        with app.app_context():
            producto = Producto(
                nombre="Test",
                codigo_sku="TEST-001",
                categoria="medicamento",
                precio_unitario=10.0,
                condiciones_almacenamiento="Test",
                fecha_vencimiento=datetime(2026, 12, 31).date(),
                proveedor_id=1,
                usuario_registro="test@test.com"
            )
            producto.desactivar()
            assert producto.estado == "Inactivo"
            assert producto.esta_activo() == False
            
            producto.activar()
            assert producto.estado == "Activo"
            assert producto.esta_activo() == True


class TestProductoValidator:
    """Tests para validadores de producto"""
    
    def test_validar_campos_obligatorios_completos(self):
        """Test validación exitosa de campos obligatorios"""
        data = {
            'nombre': 'Test',
            'codigo_sku': 'TEST-001',
            'categoria': 'medicamento',
            'precio_unitario': '10.50',
            'condiciones_almacenamiento': 'Frío',
            'fecha_vencimiento': '31/12/2026',
            'proveedor_id': '1',
            'usuario_registro': 'test@test.com',
            'tipo_certificacion': 'INVIMA',
            'fecha_vencimiento_cert': '31/12/2027'
        }
        # No debe lanzar excepción
        ProductoValidator.validar_campos_obligatorios(data)
    
    def test_validar_campos_obligatorios_faltantes(self):
        """Test validación con campos faltantes"""
        data = {'nombre': 'Test'}
        with pytest.raises(ValueError) as exc_info:
            ProductoValidator.validar_campos_obligatorios(data)
        error = exc_info.value.args[0]
        assert 'Faltan campos obligatorios' in error['error']
    
    def test_validar_sku_valido(self):
        """Test validación de SKU válido"""
        ProductoValidator.validar_formato_sku("MED-PARA-500")
        ProductoValidator.validar_formato_sku("TEST123")
        ProductoValidator.validar_formato_sku("ABC_XYZ-123")
    
    def test_validar_sku_invalido(self):
        """Test validación de SKU inválido"""
        with pytest.raises(ValueError) as exc_info:
            ProductoValidator.validar_formato_sku("AB")  # Muy corto
        error = exc_info.value.args[0]
        assert 'SKU_FORMATO_INVALIDO' in error['codigo']
    
    def test_validar_categoria_valida(self):
        """Test validación de categoría válida"""
        for categoria in CATEGORIAS_VALIDAS:
            ProductoValidator.validar_categoria(categoria)
    
    def test_validar_categoria_invalida(self):
        """Test validación de categoría inválida"""
        with pytest.raises(ValueError) as exc_info:
            ProductoValidator.validar_categoria("categoria_invalida")
        error = exc_info.value.args[0]
        assert 'CATEGORIA_INVALIDA' in error['codigo']
    
    def test_validar_precio_valido(self):
        """Test validación de precio válido"""
        ProductoValidator.validar_precio("10.50")
        ProductoValidator.validar_precio(25.99)
    
    def test_validar_precio_invalido(self):
        """Test validación de precio inválido"""
        with pytest.raises(ValueError):
            ProductoValidator.validar_precio("-5")
        
        with pytest.raises(ValueError):
            ProductoValidator.validar_precio("abc")
    
    def test_validar_fecha_valida(self):
        """Test validación de fecha válida"""
        fecha = ProductoValidator.validar_fecha("31/12/2026", "test")
        assert fecha.year == 2026
        assert fecha.month == 12
        assert fecha.day == 31
    
    def test_validar_fecha_invalida(self):
        """Test validación de fecha inválida"""
        with pytest.raises(ValueError) as exc_info:
            ProductoValidator.validar_fecha("2026-12-31", "test")
        error = exc_info.value.args[0]
        assert 'FECHA_FORMATO_INVALIDO' in error['codigo']


class TestCertificacionValidator:
    """Tests para validadores de certificación"""
    
    def test_validar_archivo_valido(self):
        """Test validación de archivo válido"""
        mock_file = MagicMock()
        mock_file.filename = 'certificado.pdf'
        mock_file.seek = MagicMock()
        mock_file.tell = MagicMock(return_value=1024)
        
        assert CertificacionValidator.validar_archivo(mock_file) == True
    
    def test_validar_archivo_sin_nombre(self):
        """Test validación sin archivo"""
        mock_file = MagicMock()
        mock_file.filename = ''
        
        with pytest.raises(ValueError) as exc_info:
            CertificacionValidator.validar_archivo(mock_file)
        error = exc_info.value.args[0]
        assert 'CERTIFICACION_REQUERIDA' in error['codigo']
    
    def test_validar_archivo_extension_invalida(self):
        """Test validación con extensión inválida"""
        mock_file = MagicMock()
        mock_file.filename = 'documento.txt'
        
        with pytest.raises(ValueError) as exc_info:
            CertificacionValidator.validar_archivo(mock_file)
        error = exc_info.value.args[0]
        assert 'ARCHIVO_EXTENSION_INVALIDA' in error['codigo']


class TestProductoService:
    """Tests para el servicio de productos"""
    
    def test_crear_producto_exitoso(self, app):
        """Test creación exitosa de producto"""
        with app.app_context():
            data = {
                'nombre': 'Paracetamol 500mg',
                'codigo_sku': 'MED-PARA-500',
                'categoria': 'medicamento',
                'precio_unitario': '25.50',
                'condiciones_almacenamiento': 'Lugar fresco y seco',
                'fecha_vencimiento': '31/12/2026',
                'proveedor_id': '1',
                'usuario_registro': 'admin@medisupply.com',
                'tipo_certificacion': 'INVIMA',
                'fecha_vencimiento_cert': '31/12/2027'
            }
            
            mock_file = MagicMock()
            mock_file.filename = 'invima_cert.pdf'
            mock_file.content_length = 1024
            mock_file.seek = MagicMock()
            mock_file.tell = MagicMock(return_value=1024)
            mock_file.save = MagicMock()
            
            with patch('os.path.getsize', return_value=1024):
                producto = ProductoService.crear_producto(data, [mock_file])
            
            assert producto.nombre == 'Paracetamol 500mg'
            assert producto.codigo_sku == 'MED-PARA-500'
            assert producto.estado == 'Activo'
            assert producto.certificacion is not None
    
    def test_crear_producto_sku_duplicado(self, app):
        """Test crear producto con SKU duplicado"""
        with app.app_context():
            data = {
                'nombre': 'Test',
                'codigo_sku': 'DUPLICATE-001',
                'categoria': 'medicamento',
                'precio_unitario': '10.0',
                'condiciones_almacenamiento': 'Test',
                'fecha_vencimiento': '31/12/2026',
                'proveedor_id': '1',
                'usuario_registro': 'test@test.com',
                'tipo_certificacion': 'INVIMA',
                'fecha_vencimiento_cert': '31/12/2027'
            }
            
            mock_file = MagicMock()
            mock_file.filename = 'test.pdf'
            mock_file.content_length = 1024
            mock_file.seek = MagicMock()
            mock_file.tell = MagicMock(return_value=1024)
            mock_file.save = MagicMock()
            
            # Crear primer producto
            with patch('os.path.getsize', return_value=1024):
                ProductoService.crear_producto(data, [mock_file])
            
            # Intentar crear segundo producto con mismo SKU
            with patch('os.path.getsize', return_value=1024):
                with pytest.raises(ConflictError) as exc_info:
                    ProductoService.crear_producto(data, [mock_file])
                error = exc_info.value.args[0]
                assert 'SKU_DUPLICADO' in error['codigo']


class TestProductoEndpoints:
    """Tests para los endpoints REST"""
    
    def test_health_check(self, client):
        """Test endpoint de health check"""
        response = client.get('/api/productos/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['servicio'] == 'Productos Microservice'
        assert data['estado'] == 'activo'
    
    def test_registrar_producto_exitoso(self, client):
        """Test registro exitoso de producto"""
        data = {
            'nombre': 'Ibuprofeno 400mg',
            'codigo_sku': 'MED-IBU-400',
            'categoria': 'medicamento',
            'precio_unitario': '15.75',
            'condiciones_almacenamiento': 'Temperatura ambiente',
            'fecha_vencimiento': '31/12/2026',
            'proveedor_id': '1',
            'usuario_registro': 'admin@medisupply.com',
            'tipo_certificacion': 'INVIMA',
            'fecha_vencimiento_cert': '31/12/2027'
        }
        
        file_obj = BytesIO(b"contenido del certificado PDF")
        data['certificacion'] = (file_obj, 'invima.pdf')
        
        response = client.post('/api/productos/',
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 201
        response_data = response.get_json()
        assert response_data['mensaje'] == 'Producto registrado exitosamente'
        assert response_data['producto']['codigo_sku'] == 'MED-IBU-400'
    
    def test_registrar_producto_sin_certificacion(self, client):
        """Test registro sin certificación"""
        data = {
            'nombre': 'Test',
            'codigo_sku': 'TEST-001',
            'categoria': 'medicamento',
            'precio_unitario': '10.0',
            'condiciones_almacenamiento': 'Test',
            'fecha_vencimiento': '31/12/2026',
            'proveedor_id': '1',
            'usuario_registro': 'test@test.com',
            'tipo_certificacion': 'INVIMA',
            'fecha_vencimiento_cert': '31/12/2027'
        }
        
        response = client.post('/api/productos/',
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'CERTIFICACION_REQUERIDA' in response_data['codigo']
    
    def test_registrar_producto_categoria_invalida(self, client):
        """Test registro con categoría inválida"""
        data = {
            'nombre': 'Test',
            'codigo_sku': 'TEST-002',
            'categoria': 'categoria_invalida',
            'precio_unitario': '10.0',
            'condiciones_almacenamiento': 'Test',
            'fecha_vencimiento': '31/12/2026',
            'proveedor_id': '1',
            'usuario_registro': 'test@test.com',
            'tipo_certificacion': 'INVIMA',
            'fecha_vencimiento_cert': '31/12/2027'
        }
        
        file_obj = BytesIO(b"test")
        data['certificacion'] = (file_obj, 'test.pdf')
        
        response = client.post('/api/productos/',
                             data=data,
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'CATEGORIA_INVALIDA' in response_data['codigo']
