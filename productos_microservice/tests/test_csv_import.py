import pytest
import io
from werkzeug.datastructures import FileStorage
from app.services.csv_service import CSVProductoService, CSVImportError
from app.models.producto import Producto


class TestCSVProductoService:
    """Tests para el servicio de importación de productos desde CSV"""
    
    def test_validar_csv_formato_archivo_valido(self):
        """Test: validar formato de archivo CSV válido"""
        # Arrange
        csv_content = b"nombre,codigo_sku\nProducto,SKU-001"
        archivo = FileStorage(
            stream=io.BytesIO(csv_content),
            filename="productos.csv",
            content_type="text/csv"
        )
        
        # Act & Assert - No debe lanzar excepción
        CSVProductoService.validar_csv_formato(archivo)
    
    def test_validar_csv_formato_sin_archivo(self):
        """Test: validar que se rechace cuando no hay archivo"""
        # Act & Assert
        with pytest.raises(CSVImportError) as excinfo:
            CSVProductoService.validar_csv_formato(None)
        
        error = excinfo.value.args[0]
        assert error['codigo'] == 'ARCHIVO_FALTANTE'
    
    def test_validar_csv_formato_extension_invalida(self):
        """Test: validar que se rechace archivo con extensión incorrecta"""
        # Arrange
        archivo = FileStorage(
            stream=io.BytesIO(b"contenido"),
            filename="productos.txt",
            content_type="text/plain"
        )
        
        # Act & Assert
        with pytest.raises(CSVImportError) as excinfo:
            CSVProductoService.validar_csv_formato(archivo)
        
        error = excinfo.value.args[0]
        assert error['codigo'] == 'FORMATO_INVALIDO'
    
    def test_leer_csv_con_todas_columnas_requeridas(self):
        """Test: leer CSV con todas las columnas requeridas"""
        # Arrange
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id
Producto 1,SKU-001,medicamento,10.50,Ambiente,31/12/2025,1
Producto 2,SKU-002,insumo,5.00,Refrigerado,30/06/2026,2"""
        
        archivo = FileStorage(
            stream=io.BytesIO(csv_content.encode('utf-8')),
            filename="productos.csv",
            content_type="text/csv"
        )
        
        # Act
        productos = CSVProductoService.leer_y_validar_csv(archivo)
        
        # Assert
        assert len(productos) == 2
        assert productos[0]['nombre'] == 'Producto 1'
        assert productos[0]['codigo_sku'] == 'SKU-001'
        assert productos[0]['_fila'] == 2
        assert productos[1]['nombre'] == 'Producto 2'
        assert productos[1]['_fila'] == 3
    
    def test_leer_csv_con_columnas_faltantes(self):
        """Test: rechazar CSV con columnas faltantes"""
        # Arrange
        csv_content = """nombre,codigo_sku
Producto 1,SKU-001"""
        
        archivo = FileStorage(
            stream=io.BytesIO(csv_content.encode('utf-8')),
            filename="productos.csv",
            content_type="text/csv"
        )
        
        # Act & Assert
        with pytest.raises(CSVImportError) as excinfo:
            CSVProductoService.leer_y_validar_csv(archivo)
        
        error = excinfo.value.args[0]
        assert error['codigo'] == 'COLUMNAS_FALTANTES'
        assert 'categoria' in error['columnas_faltantes']
    
    def test_leer_csv_vacio(self):
        """Test: rechazar CSV sin datos"""
        # Arrange
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id"""
        
        archivo = FileStorage(
            stream=io.BytesIO(csv_content.encode('utf-8')),
            filename="productos.csv",
            content_type="text/csv"
        )
        
        # Act & Assert
        with pytest.raises(CSVImportError) as excinfo:
            CSVProductoService.leer_y_validar_csv(archivo)
        
        error = excinfo.value.args[0]
        assert error['codigo'] == 'CSV_SIN_DATOS'
    
    def test_validar_producto_csv_datos_validos(self):
        """Test: validar datos válidos de producto desde CSV"""
        # Arrange
        producto_data = {
            '_fila': 2,
            'nombre': 'Paracetamol 500mg',
            'codigo_sku': 'SKU-MED-001',
            'categoria': 'medicamento',
            'precio_unitario': '12.50',
            'condiciones_almacenamiento': 'Temperatura ambiente',
            'fecha_vencimiento': '31/12/2025',
            'proveedor_id': '1'
        }
        
        # Act
        resultado = CSVProductoService.validar_producto_csv(producto_data)
        
        # Assert
        assert resultado['nombre'] == 'Paracetamol 500mg'
        assert resultado['precio_unitario'] == 12.50
        assert resultado['proveedor_id'] == 1
        assert resultado['usuario_registro'] == 'sistema_csv'
        assert resultado['estado'] == 'Activo'
    
    def test_validar_producto_csv_campo_obligatorio_faltante(self):
        """Test: rechazar producto con campo obligatorio faltante"""
        # Arrange
        producto_data = {
            '_fila': 2,
            'nombre': 'Producto sin SKU',
            'codigo_sku': '',  # Vacío
            'categoria': 'medicamento',
            'precio_unitario': '12.50',
            'condiciones_almacenamiento': 'Temperatura ambiente',
            'fecha_vencimiento': '31/12/2025',
            'proveedor_id': '1'
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            CSVProductoService.validar_producto_csv(producto_data)
        
        error = excinfo.value.args[0]
        assert error['codigo'] == 'DATOS_INVALIDOS'
        assert error['fila'] == 2
    
    def test_validar_producto_csv_categoria_invalida(self):
        """Test: rechazar producto con categoría inválida"""
        # Arrange
        producto_data = {
            '_fila': 2,
            'nombre': 'Producto Test',
            'codigo_sku': 'SKU-TEST-001',
            'categoria': 'categoria_invalida',
            'precio_unitario': '12.50',
            'condiciones_almacenamiento': 'Temperatura ambiente',
            'fecha_vencimiento': '31/12/2025',
            'proveedor_id': '1'
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            CSVProductoService.validar_producto_csv(producto_data)
        
        error = excinfo.value.args[0]
        assert error['codigo'] == 'CATEGORIA_INVALIDA'
    
    def test_validar_producto_csv_precio_invalido(self):
        """Test: rechazar producto con precio inválido"""
        # Arrange
        producto_data = {
            '_fila': 2,
            'nombre': 'Producto Test',
            'codigo_sku': 'SKU-TEST-001',
            'categoria': 'medicamento',
            'precio_unitario': 'no_es_numero',
            'condiciones_almacenamiento': 'Temperatura ambiente',
            'fecha_vencimiento': '31/12/2025',
            'proveedor_id': '1'
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            CSVProductoService.validar_producto_csv(producto_data)
        
        error = excinfo.value.args[0]
        assert error['codigo'] == 'PRECIO_INVALIDO'
    
    def test_importar_productos_csv_exitoso(self, app):
        """Test: importar productos desde CSV correctamente"""
        # Arrange
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id
Paracetamol,SKU-CSV-001,medicamento,10.50,Ambiente,31/12/2025,1
Jeringa,SKU-CSV-002,insumo,2.75,Ambiente,30/06/2026,2"""
        
        archivo = FileStorage(
            stream=io.BytesIO(csv_content.encode('utf-8')),
            filename="productos.csv",
            content_type="text/csv"
        )
        
        # Act
        with app.app_context():
            resultados = CSVProductoService.importar_productos_csv(archivo, 'admin')
        
        # Assert
        assert resultados['total_filas'] == 2
        assert resultados['exitosos'] == 2
        assert resultados['fallidos'] == 0
        assert len(resultados['detalles_exitosos']) == 2
        assert len(resultados['detalles_errores']) == 0
        
        # Verificar que se crearon en la base de datos
        with app.app_context():
            producto1 = Producto.query.filter_by(codigo_sku='SKU-CSV-001').first()
            producto2 = Producto.query.filter_by(codigo_sku='SKU-CSV-002').first()
            assert producto1 is not None
            assert producto1.nombre == 'Paracetamol'
            assert producto1.usuario_registro == 'admin'
            assert producto2 is not None
            assert producto2.nombre == 'Jeringa'
    
    def test_importar_productos_csv_con_sku_duplicado(self, app):
        """Test: manejar SKU duplicado en importación CSV"""
        # Arrange - Crear producto existente
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id
Producto Nuevo,SKU-DUP-001,medicamento,10.50,Ambiente,31/12/2025,1
Producto Duplicado,SKU-DUP-001,insumo,5.00,Ambiente,30/06/2026,2"""
        
        archivo = FileStorage(
            stream=io.BytesIO(csv_content.encode('utf-8')),
            filename="productos.csv",
            content_type="text/csv"
        )
        
        # Act
        with app.app_context():
            resultados = CSVProductoService.importar_productos_csv(archivo)
        
        # Assert
        assert resultados['total_filas'] == 2
        assert resultados['exitosos'] == 1
        assert resultados['fallidos'] == 1
        assert resultados['detalles_errores'][0]['codigo'] == 'SKU_DUPLICADO'
    
    def test_importar_productos_csv_con_datos_invalidos(self, app):
        """Test: manejar filas con datos inválidos en CSV"""
        # Arrange
        csv_content = """nombre,codigo_sku,categoria,precio_unitario,condiciones_almacenamiento,fecha_vencimiento,proveedor_id
Producto Valido,SKU-VAL-001,medicamento,10.50,Ambiente,31/12/2025,1
Producto Invalido,SKU-INV-001,categoria_mala,precio_malo,Ambiente,31/12/2025,1"""
        
        archivo = FileStorage(
            stream=io.BytesIO(csv_content.encode('utf-8')),
            filename="productos.csv",
            content_type="text/csv"
        )
        
        # Act
        with app.app_context():
            resultados = CSVProductoService.importar_productos_csv(archivo)
        
        # Assert
        assert resultados['total_filas'] == 2
        assert resultados['exitosos'] == 1
        assert resultados['fallidos'] == 1
        assert len(resultados['detalles_errores']) == 1
    

    def test_validar_producto_csv_url_certificacion_invalida(self):
        """Test: rechazar URL de certificación inválida"""
        # Arrange
        producto_data = {
            '_fila': 2,
            'nombre': 'Producto Test',
            'codigo_sku': 'SKU-TEST-001',
            'categoria': 'medicamento',
            'precio_unitario': '12.50',
            'condiciones_almacenamiento': 'Temperatura ambiente',
            'fecha_vencimiento': '31/12/2025',
            'proveedor_id': '1',
            'url_certificacion': 'url_invalida_sin_protocolo'
        }
        
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            CSVProductoService.validar_producto_csv(producto_data)
        
        error = excinfo.value.args[0]
        assert error['codigo'] == 'URL_CERTIFICACION_INVALIDA'
