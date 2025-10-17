import csv
import io
from datetime import datetime
from typing import List, Dict, Any
from werkzeug.datastructures import FileStorage
from app.models.producto import Producto, CertificacionProducto, CATEGORIAS_VALIDAS
from app.utils.validators import ProductoValidator
from app.extensions import db
from sqlalchemy.exc import IntegrityError


class CSVImportError(Exception):
    """Excepción personalizada para errores en la importación de CSV"""
    pass


class CSVProductoService:
    """Servicio para importación masiva de productos desde CSV"""
    
    # Columnas requeridas en el CSV
    COLUMNAS_REQUERIDAS = [
        'nombre',
        'codigo_sku',
        'categoria',
        'precio_unitario',
        'condiciones_almacenamiento',
        'fecha_vencimiento',
        'proveedor_id'
    ]
    
    # Columnas opcionales
    COLUMNAS_OPCIONALES = [
        'usuario_registro',
        'estado',
        'url_certificacion',
        'tipo_certificacion',
        'fecha_vencimiento_cert'
    ]
    
    @staticmethod
    def validar_csv_formato(archivo: FileStorage) -> None:
        """
        Valida el formato del archivo CSV
        
        Args:
            archivo: Archivo CSV cargado
            
        Raises:
            CSVImportError: Si el formato es inválido
        """
        if not archivo:
            raise CSVImportError({
                "error": "No se proporcionó ningún archivo",
                "codigo": "ARCHIVO_FALTANTE"
            })
        
        if not archivo.filename:
            raise CSVImportError({
                "error": "El archivo no tiene nombre",
                "codigo": "ARCHIVO_INVALIDO"
            })
        
        if not archivo.filename.endswith('.csv'):
            raise CSVImportError({
                "error": "El archivo debe ser un CSV (.csv)",
                "codigo": "FORMATO_INVALIDO",
                "formato_esperado": "csv"
            })
    
    @staticmethod
    def leer_y_validar_csv(archivo: FileStorage) -> List[Dict[str, Any]]:
        """
        Lee el archivo CSV y valida su estructura
        
        Args:
            archivo: Archivo CSV cargado
            
        Returns:
            Lista de diccionarios con los datos de los productos
            
        Raises:
            CSVImportError: Si hay errores en la estructura del CSV
        """
        try:
            # Leer el contenido del archivo
            stream = io.StringIO(archivo.stream.read().decode("UTF-8"), newline=None)
            csv_reader = csv.DictReader(stream)
            
            # Validar que tenga las columnas requeridas
            if not csv_reader.fieldnames:
                raise CSVImportError({
                    "error": "El archivo CSV está vacío o no tiene encabezados",
                    "codigo": "CSV_VACIO"
                })
            
            columnas_faltantes = set(CSVProductoService.COLUMNAS_REQUERIDAS) - set(csv_reader.fieldnames)
            if columnas_faltantes:
                raise CSVImportError({
                    "error": "El CSV no contiene todas las columnas requeridas",
                    "codigo": "COLUMNAS_FALTANTES",
                    "columnas_faltantes": list(columnas_faltantes),
                    "columnas_requeridas": CSVProductoService.COLUMNAS_REQUERIDAS
                })
            
            # Leer todas las filas
            productos = []
            for idx, row in enumerate(csv_reader, start=2):  # start=2 porque fila 1 es el encabezado
                # Filtrar valores vacíos
                row_limpia = {k: v.strip() if v else None for k, v in row.items()}
                row_limpia['_fila'] = idx  # Guardar número de fila para reportes de error
                productos.append(row_limpia)
            
            if not productos:
                raise CSVImportError({
                    "error": "El archivo CSV no contiene filas de datos",
                    "codigo": "CSV_SIN_DATOS"
                })
            
            return productos
            
        except UnicodeDecodeError:
            raise CSVImportError({
                "error": "El archivo no está codificado en UTF-8",
                "codigo": "CODIFICACION_INVALIDA",
                "codificacion_esperada": "UTF-8"
            })
        except csv.Error as e:
            raise CSVImportError({
                "error": f"Error al leer el archivo CSV: {str(e)}",
                "codigo": "ERROR_LECTURA_CSV"
            })
    
    @staticmethod
    def validar_producto_csv(producto_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida los datos de un producto del CSV
        
        Args:
            producto_data: Diccionario con datos del producto
            
        Returns:
            Diccionario con datos validados
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        fila = producto_data.get('_fila', '?')
        errores = []
        
        # Validar campos obligatorios
        for campo in CSVProductoService.COLUMNAS_REQUERIDAS:
            if not producto_data.get(campo):
                errores.append(f"Campo '{campo}' es obligatorio")
        
        if errores:
            raise ValueError({
                "error": "Datos inválidos en la fila",
                "codigo": "DATOS_INVALIDOS",
                "fila": fila,
                "detalles": errores
            })
        
        # Validar formato de SKU
        try:
            ProductoValidator.validar_formato_sku(producto_data['codigo_sku'])
        except ValueError as e:
            raise ValueError({
                "error": "SKU inválido",
                "codigo": "SKU_INVALIDO",
                "fila": fila,
                "detalles": e.args[0].get('error', str(e))
            })
        
        # Validar categoría
        if producto_data['categoria'] not in CATEGORIAS_VALIDAS:
            raise ValueError({
                "error": f"Categoría inválida: '{producto_data['categoria']}'",
                "codigo": "CATEGORIA_INVALIDA",
                "fila": fila,
                "categorias_validas": CATEGORIAS_VALIDAS
            })
        
        # Validar precio
        try:
            precio = float(producto_data['precio_unitario'])
            if precio <= 0:
                raise ValueError("El precio debe ser mayor a 0")
            producto_data['precio_unitario'] = precio
        except (ValueError, TypeError):
            raise ValueError({
                "error": "Precio unitario inválido (debe ser un número positivo)",
                "codigo": "PRECIO_INVALIDO",
                "fila": fila,
                "valor": producto_data['precio_unitario']
            })
        
        # Validar proveedor_id
        try:
            producto_data['proveedor_id'] = int(producto_data['proveedor_id'])
        except (ValueError, TypeError):
            raise ValueError({
                "error": "ID de proveedor inválido (debe ser un número entero)",
                "codigo": "PROVEEDOR_ID_INVALIDO",
                "fila": fila,
                "valor": producto_data['proveedor_id']
            })
        
        # Validar fecha de vencimiento
        try:
            fecha_venc = ProductoValidator.validar_fecha(
                producto_data['fecha_vencimiento'],
                'fecha_vencimiento'
            )
            producto_data['fecha_vencimiento'] = fecha_venc
        except ValueError as e:
            raise ValueError({
                "error": "Fecha de vencimiento inválida",
                "codigo": "FECHA_INVALIDA",
                "fila": fila,
                "detalles": e.args[0].get('error', str(e))
            })
        
        # Establecer valores por defecto
        producto_data['usuario_registro'] = producto_data.get('usuario_registro', 'sistema_csv')
        producto_data['estado'] = producto_data.get('estado', 'Activo')
        
        # Validar estado
        if producto_data['estado'] not in ['Activo', 'Inactivo']:
            raise ValueError({
                "error": "Estado inválido (debe ser 'Activo' o 'Inactivo')",
                "codigo": "ESTADO_INVALIDO",
                "fila": fila,
                "valor": producto_data['estado']
            })
        
        # Validar URL de certificación si se proporciona
        url_certificacion = producto_data.get('url_certificacion', '').strip()
        if url_certificacion:
            # Validar formato de URL básico
            if not (url_certificacion.startswith('http://') or url_certificacion.startswith('https://')):
                raise ValueError({
                    "error": "URL de certificación debe comenzar con http:// o https://",
                    "codigo": "URL_CERTIFICACION_INVALIDA",
                    "fila": fila,
                    "valor": url_certificacion
                })
            
            # Si hay URL, validar campos relacionados
            tipo_cert = producto_data.get('tipo_certificacion', '').strip()
            if not tipo_cert:
                # Establecer tipo por defecto
                producto_data['tipo_certificacion'] = 'INVIMA'
            
            # Validar fecha de vencimiento de certificación
            fecha_venc_cert = producto_data.get('fecha_vencimiento_cert', '').strip()
            if fecha_venc_cert:
                try:
                    fecha_cert = ProductoValidator.validar_fecha(
                        fecha_venc_cert,
                        'fecha_vencimiento_cert'
                    )
                    producto_data['fecha_vencimiento_cert'] = fecha_cert
                except ValueError:
                    raise ValueError({
                        "error": "Fecha de vencimiento de certificación inválida",
                        "codigo": "FECHA_CERT_INVALIDA",
                        "fila": fila,
                        "valor": fecha_venc_cert
                    })
            else:
                # Si no se proporciona fecha, usar la misma del producto
                producto_data['fecha_vencimiento_cert'] = producto_data['fecha_vencimiento']
        
        return producto_data
    
    @staticmethod
    def importar_productos_csv(archivo: FileStorage, usuario_importacion: str = None) -> Dict[str, Any]:
        """
        Importa productos desde un archivo CSV
        
        Args:
            archivo: Archivo CSV con los productos
            usuario_importacion: Usuario que realiza la importación (opcional)
            
        Returns:
            Diccionario con el resultado de la importación
            
        Raises:
            CSVImportError: Si hay errores en el formato del CSV
        """
        # Validar formato del archivo
        CSVProductoService.validar_csv_formato(archivo)
        
        # Leer y validar estructura del CSV
        productos_data = CSVProductoService.leer_y_validar_csv(archivo)
        
        resultados = {
            "total_filas": len(productos_data),
            "exitosos": 0,
            "fallidos": 0,
            "detalles_exitosos": [],
            "detalles_errores": []
        }
        
        # Procesar cada producto
        for producto_data in productos_data:
            fila = producto_data['_fila']
            sku = producto_data.get('codigo_sku', 'N/A')
            
            try:
                # Validar datos del producto
                datos_validados = CSVProductoService.validar_producto_csv(producto_data)
                
                # Sobrescribir usuario_registro si se proporciona
                if usuario_importacion:
                    datos_validados['usuario_registro'] = usuario_importacion
                
                # Verificar que el SKU no exista
                if Producto.query.filter_by(codigo_sku=sku).first():
                    resultados['fallidos'] += 1
                    resultados['detalles_errores'].append({
                        "fila": fila,
                        "sku": sku,
                        "error": f"Ya existe un producto con el SKU {sku}",
                        "codigo": "SKU_DUPLICADO"
                    })
                    continue
                
                # Crear producto
                producto = Producto(
                    nombre=datos_validados['nombre'],
                    codigo_sku=datos_validados['codigo_sku'],
                    categoria=datos_validados['categoria'],
                    precio_unitario=datos_validados['precio_unitario'],
                    condiciones_almacenamiento=datos_validados['condiciones_almacenamiento'],
                    fecha_vencimiento=datos_validados['fecha_vencimiento'],
                    proveedor_id=datos_validados['proveedor_id'],
                    usuario_registro=datos_validados['usuario_registro'],
                    estado=datos_validados['estado']
                )
                
                db.session.add(producto)
                db.session.flush()  # Para obtener el ID
                
                # Crear certificación desde URL si se proporciona
                url_certificacion = datos_validados.get('url_certificacion', '').strip()
                if url_certificacion:
                    certificacion = CertificacionProducto(
                        producto_id=producto.id,
                        tipo_certificacion=datos_validados.get('tipo_certificacion', 'INVIMA'),
                        nombre_archivo=f"certificacion_url_{producto.codigo_sku}",
                        ruta_archivo=url_certificacion,  # Guardamos la URL en lugar de ruta local
                        tamaño_archivo=0,  # No aplica para URLs
                        fecha_vencimiento_cert=datos_validados['fecha_vencimiento_cert']
                    )
                    db.session.add(certificacion)
                
                resultados['exitosos'] += 1
                detalle_exitoso = {
                    "fila": fila,
                    "sku": sku,
                    "nombre": producto.nombre,
                    "id": producto.id,
                    "tiene_certificacion": bool(url_certificacion)
                }
                
                # Agregar detalles de certificación si existe
                if url_certificacion:
                    detalle_exitoso["certificacion"] = {
                        "tipo": datos_validados.get('tipo_certificacion', 'INVIMA'),
                        "url": url_certificacion,
                        "fecha_vencimiento": datos_validados['fecha_vencimiento_cert'].strftime("%d/%m/%Y")
                    }
                
                resultados['detalles_exitosos'].append(detalle_exitoso)
                
            except ValueError as e:
                resultados['fallidos'] += 1
                error_data = e.args[0] if e.args and isinstance(e.args[0], dict) else {"error": str(e)}
                error_data['fila'] = fila
                error_data['sku'] = sku
                resultados['detalles_errores'].append(error_data)
                
            except Exception as e:
                resultados['fallidos'] += 1
                resultados['detalles_errores'].append({
                    "fila": fila,
                    "sku": sku,
                    "error": f"Error inesperado: {str(e)}",
                    "codigo": "ERROR_INESPERADO"
                })
        
        # Commit si hay al menos un producto exitoso
        if resultados['exitosos'] > 0:
            try:
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                raise CSVImportError({
                    "error": "Error al guardar los productos en la base de datos",
                    "codigo": "ERROR_BASE_DATOS",
                    "detalles": str(e)
                })
        else:
            db.session.rollback()
        
        return resultados
