from app.models.proveedor import Proveedor, Certificacion
from app.extensions import db
from app.utils.validators import ProveedorValidator, CertificacionValidator
from sqlalchemy.exc import IntegrityError
import os
import uuid
from werkzeug.utils import secure_filename

class ConflictError(Exception):
    """Excepción personalizada para conflictos (409)"""
    pass

class ProveedorService:

    @staticmethod
    def crear_proveedor(data, archivos_certificacion=None):
        """Crea un nuevo proveedor con validaciones completas"""
        
        # 1. Validar campos obligatorios
        errores = ProveedorValidator.validar_campos_obligatorios(data)
        if errores:
            raise ValueError({"errores": errores})
        
        # 2. Validar formato de NIT
        es_valido, mensaje = ProveedorValidator.validar_formato_nit(data.get('nit'))
        if not es_valido:
            raise ValueError({"error": mensaje})
        
        # 3. Validar email
        if data.get('email'):
            es_valido, mensaje = ProveedorValidator.validar_email(data['email'])
            if not es_valido:
                raise ValueError({"error": mensaje})
        
        # 4. Validar teléfono
        if data.get('telefono'):
            es_valido, mensaje = ProveedorValidator.validar_telefono(data['telefono'])
            if not es_valido:
                raise ValueError({"error": mensaje})
        
        # 5. Validar certificaciones obligatorias PRIMERO
        if not archivos_certificacion or len(archivos_certificacion) == 0:
            raise ValueError({"error": "Debe adjuntar al menos una certificación sanitaria"})
        
        # 6. Validar TODOS los archivos ANTES de tocar la base de datos
        for i, archivo in enumerate(archivos_certificacion):
            es_valido, mensaje = CertificacionValidator.validar_archivo(archivo)
            if not es_valido:
                raise ValueError({"error": f"Archivo {i+1} '{archivo.filename}': {mensaje}"})
        
        # 7. Verificar duplicado de NIT ANTES de crear en DB
        if ProveedorService._verificar_nit_existe(data.get('nit')):
            raise ConflictError({"error": f"Ya existe un proveedor registrado con el NIT {data['nit']}"})
        
        try:
            # 8. SOLO AHORA crear el proveedor (todas las validaciones pasaron)
            proveedor = Proveedor(
                nombre=data['nombre'],
                nit=data['nit'],
                pais=data['pais'],
                estado='Activo',  # Todos los proveedores se registran como Activos por defecto
                direccion=data['direccion'],
                nombre_contacto=data['nombre_contacto'],
                email=data['email'],
                telefono=data['telefono']
            )
            
            db.session.add(proveedor)
            db.session.flush()  # Para obtener el ID sin hacer commit
            
            # 9. Guardar certificaciones (archivos ya validados)
            certificaciones_guardadas = []
            for archivo in archivos_certificacion:
                certificacion = ProveedorService._guardar_certificacion(proveedor.id, archivo)
                certificaciones_guardadas.append(certificacion)
            
            db.session.commit()
            return proveedor
            
        except IntegrityError as e:
            db.session.rollback()
            if 'nit' in str(e):
                raise ConflictError({"error": f"Ya existe un proveedor registrado con el NIT {data['nit']}"})
            raise ValueError({"error": "Error al guardar el proveedor en la base de datos"})
        
        except Exception as e:
            db.session.rollback()
            raise ValueError({"error": f"Error inesperado: {str(e)}"})
    
    @staticmethod
    def _verificar_nit_existe(nit):
        """Verifica si ya existe un proveedor con el NIT dado"""
        return Proveedor.query.filter_by(nit=nit).first() is not None

    @staticmethod
    def _guardar_certificacion(proveedor_id, archivo):
        """Guarda un archivo de certificación en el sistema de archivos"""
        
        # Crear directorio si no existe
        upload_dir = os.path.join('uploads', 'certificaciones', str(proveedor_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        filename = secure_filename(archivo.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Guardar archivo
        archivo.save(file_path)
        
        # Crear registro en base de datos
        certificacion = Certificacion(
            proveedor_id=proveedor_id,
            nombre_archivo=filename,
            ruta_archivo=file_path,
            tipo_certificacion='sanitaria',
            tamaño_archivo=os.path.getsize(file_path)
        )
        
        db.session.add(certificacion)
        return certificacion
