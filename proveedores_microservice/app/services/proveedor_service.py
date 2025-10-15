from app.models.proveedor import Proveedor, Certificacion
from app.extensions import db
from app.utils.validators import ProveedorValidator, CertificacionValidator
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_
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

    @staticmethod
    def listar_proveedores(filtros=None, pagina=1, por_pagina=20):
        """
        Lista proveedores con búsqueda y filtros optimizados según HU KAN-92
        
        Filtros soportados:
        - nombre: Búsqueda parcial en nombre del proveedor (case-insensitive)
        - pais: País exacto (case-insensitive)
        - estado_certificacion: 'vigente', 'vencida', 'en_revision', 'sin_certificaciones'
        - estado: 'Activo' o 'Inactivo'
        
        Args:
            filtros (dict): Diccionario con los filtros a aplicar
            pagina (int): Número de página (default: 1)
            por_pagina (int): Items por página (default: 20, max: 100)
        
        Returns:
            dict: {
                'proveedores': [...],
                'total': int,
                'pagina': int,
                'por_pagina': int,
                'total_paginas': int
            }
        """
        if filtros is None:
            filtros = {}
        
        # Query base
        query = Proveedor.query
        
        # Filtro por nombre (búsqueda parcial, case-insensitive)
        if filtros.get('nombre'):
            query = query.filter(Proveedor.nombre.ilike(f"%{filtros['nombre']}%"))
        
        # Filtro por país (exacto, case-insensitive)
        if filtros.get('pais'):
            query = query.filter(Proveedor.pais.ilike(filtros['pais']))
        
        # Filtro por estado del proveedor
        if filtros.get('estado'):
            if filtros['estado'] in ['Activo', 'Inactivo']:
                query = query.filter(Proveedor.estado == filtros['estado'])
        
        # Filtro por estado de certificaciones
        if filtros.get('estado_certificacion'):
            query = ProveedorService._aplicar_filtro_certificacion(
                query, 
                filtros['estado_certificacion']
            )
        
        # Ordenamiento por defecto: nombre ascendente
        query = query.order_by(Proveedor.nombre.asc())
        
        # Paginación
        paginacion = query.paginate(
            page=pagina,
            per_page=por_pagina,
            error_out=False
        )
        
        # Enriquecer cada proveedor con estado de certificaciones
        proveedores_enriquecidos = []
        for proveedor in paginacion.items:
            proveedor_dict = {
                'id': proveedor.id,
                'nombre': proveedor.nombre,
                'nit': proveedor.nit,
                'pais': proveedor.pais,
                'estado': proveedor.estado,
                'email': proveedor.email,
                'telefono': proveedor.telefono,
                'nombre_contacto': proveedor.nombre_contacto,
                'direccion': proveedor.direccion,
                'estado_certificacion': ProveedorService._obtener_estado_certificacion(proveedor),
                'total_certificaciones': len(proveedor.certificaciones),
                'fecha_registro': proveedor.fecha_registro.isoformat() if proveedor.fecha_registro else None
            }
            proveedores_enriquecidos.append(proveedor_dict)
        
        return {
            'proveedores': proveedores_enriquecidos,
            'total': paginacion.total,
            'pagina': paginacion.page,
            'por_pagina': paginacion.per_page,
            'total_paginas': paginacion.pages
        }
    
    @staticmethod
    def _aplicar_filtro_certificacion(query, estado_certificacion):
        """
        Aplica filtro según el estado de certificaciones
        
        Estados soportados:
        - 'vigente': Tiene certificaciones (simulado por ahora)
        - 'sin_certificaciones': No tiene certificaciones
        - 'vencida': Para implementación futura con fechas de vencimiento
        - 'en_revision': Para implementación futura con workflow de revisión
        
        Args:
            query: Query de SQLAlchemy
            estado_certificacion (str): Estado a filtrar
        
        Returns:
            Query modificada con el filtro aplicado
        """
        if estado_certificacion == 'vigente':
            # Tiene al menos una certificación
            query = query.join(Certificacion).distinct()
        elif estado_certificacion == 'sin_certificaciones':
            # No tiene certificaciones
            query = query.filter(~Proveedor.certificaciones.any())
        elif estado_certificacion == 'vencida':
            # Futuro: filtrar por certificaciones con fecha_vencimiento < hoy
            # Por ahora retornamos query sin cambios
            pass
        elif estado_certificacion == 'en_revision':
            # Futuro: filtrar por certificaciones con estado='en_revision'
            # Por ahora retornamos query sin cambios
            pass
        
        return query
    
    @staticmethod
    def _obtener_estado_certificacion(proveedor):
        """
        Determina el estado de las certificaciones de un proveedor
        
        Estados posibles:
        - 'vigente': Tiene certificaciones activas
        - 'vencida': Tiene certificaciones vencidas (futuro)
        - 'en_revision': Certificaciones en proceso de revisión (futuro)
        - 'sin_certificaciones': No tiene ninguna certificación
        
        Args:
            proveedor: Instancia del modelo Proveedor
        
        Returns:
            str: Estado de certificación
        """
        if not proveedor.certificaciones or len(proveedor.certificaciones) == 0:
            return 'sin_certificaciones'
        
        # Por ahora, si tiene certificaciones se considera 'vigente'
        # Futuro: implementar lógica de validación de fechas de vencimiento
        # y estados de revisión
        return 'vigente'
    
    @staticmethod
    def obtener_proveedor_por_id(proveedor_id):
        """
        Obtiene un proveedor por ID con toda su información completa
        según requerimientos de HU KAN-92
        
        Incluye:
        - Información fiscal validada (NIT, régimen, país)
        - Datos de contacto completos
        - Certificaciones adjuntas con fechas
        - Estado del proveedor
        
        Args:
            proveedor_id (int): ID del proveedor
        
        Returns:
            dict: Información completa del proveedor con certificaciones
        
        Raises:
            ValueError: Si el proveedor no existe
        """
        proveedor = db.session.get(Proveedor, proveedor_id)
        
        if not proveedor:
            raise ValueError({"error": "Proveedor no encontrado"})
        
        # Información completa del proveedor según especificación HU
        proveedor_detalle = {
            # Identificación y datos básicos
            'id': proveedor.id,
            'nombre': proveedor.nombre,
            'estado': proveedor.estado,
            'fecha_registro': proveedor.fecha_registro.isoformat() if proveedor.fecha_registro else None,
            
            # Información fiscal
            'informacion_fiscal': {
                'nit': proveedor.nit,
                'pais': proveedor.pais,
                'regimen': 'Común'  # Futuro: agregar campo régimen al modelo
            },
            
            # Datos de contacto completos
            'contacto': {
                'nombre_contacto': proveedor.nombre_contacto,
                'email': proveedor.email,
                'telefono': proveedor.telefono,
                'direccion': proveedor.direccion
            },
            
            # Estado de certificaciones
            'estado_certificacion': ProveedorService._obtener_estado_certificacion(proveedor),
            
            # Certificaciones adjuntas con información detallada
            'certificaciones': [
                {
                    'id': cert.id,
                    'nombre_archivo': cert.nombre_archivo,
                    'tipo_certificacion': cert.tipo_certificacion,
                    'tamaño_archivo': cert.tamaño_archivo,
                    'tamaño_mb': round(cert.tamaño_archivo / (1024 * 1024), 2),
                    'fecha_subida': cert.fecha_subida.isoformat() if cert.fecha_subida else None
                }
                for cert in proveedor.certificaciones
            ],
            
            # Historial de compras (futuro: implementar relación con órdenes de compra)
            'historial_compras': {
                'total_ordenes': 0,  # Futuro: contar órdenes de compra
                'monto_total': 0.0,  # Futuro: sumar montos
                'ultima_compra': None  # Futuro: fecha de última orden
            }
        }
        
        return proveedor_detalle
