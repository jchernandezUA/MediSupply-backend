import re
from datetime import datetime
from werkzeug.utils import secure_filename

class ProductoValidator:
    """Validador para datos de producto"""
    
    CATEGORIAS_VALIDAS = ['medicamento', 'insumo', 'reactivo', 'dispositivo']
    CERTIFICACIONES_VALIDAS = ['INVIMA', 'FDA', 'EMA']
    
    @staticmethod
    def validar_campos_obligatorios(data):
        """Valida que todos los campos obligatorios estén presentes"""
        campos_requeridos = [
            'nombre', 'codigo_sku', 'categoria', 'precio_unitario',
            'condiciones_almacenamiento', 'fecha_vencimiento',
            'proveedor_id', 'usuario_registro', 'tipo_certificacion',
            'fecha_vencimiento_cert'
        ]
        
        campos_faltantes = [campo for campo in campos_requeridos if not data.get(campo)]
        
        if campos_faltantes:
            raise ValueError({
                "error": f"Faltan campos obligatorios: {', '.join(campos_faltantes)}",
                "codigo": "CAMPOS_FALTANTES",
                "campos_requeridos": campos_requeridos
            })
        
        # Validar que los campos no estén vacíos
        for campo in campos_requeridos:
            valor = data.get(campo)
            if isinstance(valor, str) and not valor.strip():
                raise ValueError({
                    "error": f"El campo '{campo}' no puede estar vacío",
                    "codigo": "CAMPO_VACIO"
                })
    
    @staticmethod
    def validar_formato_sku(sku):
        """Valida el formato del código SKU"""
        if not sku or not isinstance(sku, str):
            raise ValueError({
                "error": "El código SKU es requerido y debe ser texto",
                "codigo": "SKU_INVALIDO"
            })
        
        # SKU debe tener entre 3 y 50 caracteres alfanuméricos
        if not re.match(r'^[A-Za-z0-9\-_]{3,50}$', sku):
            raise ValueError({
                "error": "El código SKU debe tener entre 3 y 50 caracteres alfanuméricos (puede incluir - y _)",
                "codigo": "SKU_FORMATO_INVALIDO",
                "valor_recibido": sku
            })
    
    @staticmethod
    def validar_categoria(categoria):
        """Valida que la categoría sea una de las permitidas"""
        if categoria not in ProductoValidator.CATEGORIAS_VALIDAS:
            raise ValueError({
                "error": f"La categoría '{categoria}' no es válida",
                "codigo": "CATEGORIA_INVALIDA",
                "categorias_validas": ProductoValidator.CATEGORIAS_VALIDAS
            })
    
    @staticmethod
    def validar_precio(precio):
        """Valida que el precio sea un número positivo"""
        try:
            precio_float = float(precio)
            if precio_float <= 0:
                raise ValueError({
                    "error": "El precio debe ser mayor a 0",
                    "codigo": "PRECIO_INVALIDO"
                })
        except (ValueError, TypeError):
            raise ValueError({
                "error": "El precio debe ser un número válido",
                "codigo": "PRECIO_FORMATO_INVALIDO"
            })
    
    @staticmethod
    def validar_fecha(fecha_str, nombre_campo="fecha"):
        """Valida formato de fecha DD/MM/YYYY"""
        try:
            # Intentar parsear la fecha en formato DD/MM/YYYY
            fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()
            return fecha
        except (ValueError, TypeError):
            raise ValueError({
                "error": f"El formato de {nombre_campo} debe ser DD/MM/YYYY",
                "codigo": "FECHA_FORMATO_INVALIDO",
                "valor_recibido": fecha_str
            })
    
    @staticmethod
    def validar_tipo_certificacion(tipo):
        """Valida que el tipo de certificación sea válido"""
        if tipo not in ProductoValidator.CERTIFICACIONES_VALIDAS:
            raise ValueError({
                "error": f"El tipo de certificación '{tipo}' no es válido",
                "codigo": "CERTIFICACION_INVALIDA",
                "tipos_validos": ProductoValidator.CERTIFICACIONES_VALIDAS
            })


class CertificacionValidator:
    """Validador para archivos de certificación"""
    
    EXTENSIONES_PERMITIDAS = {'pdf', 'jpg', 'jpeg', 'png'}
    TAMAÑO_MAXIMO = 5 * 1024 * 1024  # 5MB en bytes
    
    @staticmethod
    def validar_archivo(archivo):
        """Valida que el archivo sea válido"""
        if not archivo or not archivo.filename:
            raise ValueError({
                "error": "Se requiere adjuntar una certificación sanitaria",
                "codigo": "CERTIFICACION_REQUERIDA"
            })
        
        # Validar extensión
        filename = secure_filename(archivo.filename)
        if '.' not in filename:
            raise ValueError({
                "error": "El archivo debe tener una extensión válida",
                "codigo": "ARCHIVO_SIN_EXTENSION"
            })
        
        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in CertificacionValidator.EXTENSIONES_PERMITIDAS:
            raise ValueError({
                "error": f"Archivo '{filename}' no tiene una extensión válida",
                "codigo": "ARCHIVO_EXTENSION_INVALIDA",
                "extensiones_permitidas": list(CertificacionValidator.EXTENSIONES_PERMITIDAS)
            })
        
        # Validar tamaño
        archivo.seek(0, 2)  # Ir al final del archivo
        tamaño = archivo.tell()
        archivo.seek(0)  # Volver al inicio
        
        if tamaño > CertificacionValidator.TAMAÑO_MAXIMO:
            raise ValueError({
                "error": f"El archivo excede el tamaño máximo permitido de 5MB",
                "codigo": "ARCHIVO_MUY_GRANDE",
                "tamaño_maximo": "5MB"
            })
        
        return True
    
    @staticmethod
    def validar_certificacion_requerida(archivos):
        """Valida que se haya adjuntado al menos una certificación"""
        if not archivos or len(archivos) == 0:
            raise ValueError({
                "error": "Se requiere adjuntar al menos una certificación sanitaria",
                "codigo": "CERTIFICACION_REQUERIDA"
            })
