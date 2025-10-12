from app.extensions import db
from app.models.producto import Producto, CertificacionProducto
from app.utils.validators import ProductoValidator, CertificacionValidator
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import os
import uuid


class ConflictError(Exception):
    """Excepción personalizada para conflictos (ej. SKU duplicado)"""
    pass


class ProductoService:
    """Servicio para gestión de productos"""
    
    @staticmethod
    def crear_producto(data, archivos_certificacion):
        """
        Crea un nuevo producto con su certificación
        
        Args:
            data: Diccionario con datos del producto
            archivos_certificacion: Lista de archivos de certificación
            
        Returns:
            Producto creado
            
        Raises:
            ValueError: Si los datos son inválidos
            ConflictError: Si el SKU ya existe
        """
        try:
            # 1. FAIL-FAST: Validar campos obligatorios primero
            ProductoValidator.validar_campos_obligatorios(data)
            
            # 2. Validar SKU antes de hacer operaciones costosas
            ProductoValidator.validar_formato_sku(data['codigo_sku'])
            
            # 3. Verificar que el SKU no exista (antes de validar archivos)
            if ProductoService._verificar_sku_existe(data['codigo_sku']):
                raise ConflictError({
                    "error": f"Ya existe un producto registrado con el SKU {data['codigo_sku']}",
                    "codigo": "SKU_DUPLICADO",
                    "sku": data['codigo_sku']
                })
            
            # 4. Validar categoría
            ProductoValidator.validar_categoria(data['categoria'])
            
            # 5. Validar precio
            ProductoValidator.validar_precio(data['precio_unitario'])
            
            # 6. Validar fechas
            fecha_vencimiento = ProductoValidator.validar_fecha(
                data['fecha_vencimiento'], 
                "fecha_vencimiento"
            )
            fecha_vencimiento_cert = ProductoValidator.validar_fecha(
                data['fecha_vencimiento_cert'],
                "fecha_vencimiento_cert"
            )
            
            # 7. Validar tipo de certificación
            ProductoValidator.validar_tipo_certificacion(data['tipo_certificacion'])
            
            # 8. Validar certificación
            CertificacionValidator.validar_certificacion_requerida(archivos_certificacion)
            for archivo in archivos_certificacion:
                CertificacionValidator.validar_archivo(archivo)
            
            # 9. Crear producto
            producto = Producto(
                nombre=data['nombre'],
                codigo_sku=data['codigo_sku'],
                categoria=data['categoria'],
                precio_unitario=float(data['precio_unitario']),
                condiciones_almacenamiento=data['condiciones_almacenamiento'],
                fecha_vencimiento=fecha_vencimiento,
                proveedor_id=int(data['proveedor_id']),
                usuario_registro=data['usuario_registro'],
                estado='Activo'  # Por defecto activo
            )
            
            # 10. Agregar a sesión y hacer flush para obtener el ID
            db.session.add(producto)
            db.session.flush()
            
            # 11. Guardar certificación (solo una según requisitos)
            certificacion = ProductoService._guardar_certificacion(
                producto.id,
                archivos_certificacion[0],
                data['tipo_certificacion'],
                fecha_vencimiento_cert
            )
            db.session.add(certificacion)
            
            # 12. Commit final
            db.session.commit()
            
            return producto
            
        except ConflictError:
            db.session.rollback()
            raise
            
        except ValueError:
            db.session.rollback()
            raise
            
        except IntegrityError as e:
            db.session.rollback()
            if 'codigo_sku' in str(e):
                raise ConflictError({
                    "error": f"Ya existe un producto registrado con el SKU {data['codigo_sku']}",
                    "codigo": "SKU_DUPLICADO"
                })
            raise ValueError({"error": "Error al guardar el producto en la base de datos"})
        
        except Exception as e:
            db.session.rollback()
            raise ValueError({"error": f"Error inesperado: {str(e)}"})
    
    @staticmethod
    def _verificar_sku_existe(sku):
        """Verifica si ya existe un producto con el SKU dado"""
        return Producto.query.filter_by(codigo_sku=sku).first() is not None

    @staticmethod
    def _guardar_certificacion(producto_id, archivo, tipo_certificacion, fecha_vencimiento_cert):
        """Guarda un archivo de certificación en el sistema de archivos"""
        
        # Crear directorio si no existe
        upload_dir = os.path.join('uploads', 'certificaciones_producto', str(producto_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        filename = secure_filename(archivo.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Guardar archivo
        archivo.save(file_path)
        
        # Crear registro en base de datos
        certificacion = CertificacionProducto(
            producto_id=producto_id,
            tipo_certificacion=tipo_certificacion,
            nombre_archivo=filename,
            ruta_archivo=file_path,
            tamaño_archivo=os.path.getsize(file_path),
            fecha_vencimiento_cert=fecha_vencimiento_cert
        )
        
        return certificacion
