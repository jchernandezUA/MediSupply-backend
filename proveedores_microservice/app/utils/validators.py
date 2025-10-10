import re
from werkzeug.datastructures import FileStorage

class ProveedorValidator:
    
    @staticmethod
    def validar_campos_obligatorios(data):
        """Valida que todos los campos obligatorios estén presentes"""
        campos_requeridos = ["nombre", "nit", "pais", "direccion", "nombre_contacto", "email", "telefono"]
        errores = []
        
        for campo in campos_requeridos:
            if campo not in data or not data[campo] or str(data[campo]).strip() == "":
                errores.append(f"El campo '{campo}' es obligatorio")
        
        return errores
    
    @staticmethod
    def validar_formato_nit(nit):
        """Valida el formato del NIT según estándares colombianos"""
        if not nit:
            return False, "El NIT es obligatorio"
        
        # Eliminar espacios y guiones
        nit_limpio = re.sub(r'[\s\-]', '', nit)
        
        # Validar que tenga entre 9 y 10 dígitos
        if not re.match(r'^\d{9,10}$', nit_limpio):
            return False, "El NIT debe tener entre 9 y 10 dígitos numéricos"
        
        return True, "NIT válido"
    
    @staticmethod
    def validar_email(email):
        """Valida el formato del email"""
        patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(patron_email, email):
            return False, "El formato del email no es válido"
        return True, "Email válido"
    
    @staticmethod
    def validar_telefono(telefono):
        """Valida el formato del teléfono"""
        # Permite números con espacios, guiones y paréntesis
        patron_telefono = r'^[\+]?[0-9\s\-\(\)]{7,20}$'
        if not re.match(patron_telefono, telefono):
            return False, "El formato del teléfono no es válido"
        return True, "Teléfono válido"


class CertificacionValidator:
    
    EXTENSIONES_PERMITIDAS = {'.pdf', '.jpg', '.jpeg', '.png'}
    TAMAÑO_MAXIMO = 5 * 1024 * 1024  # 5MB en bytes
    
    @staticmethod
    def validar_archivo(archivo):
        """Valida un archivo de certificación"""
        if not archivo or not hasattr(archivo, 'filename'):
            return False, "No se ha proporcionado ningún archivo"
        
        if archivo.filename == '':
            return False, "El archivo no tiene nombre"
        
        # Validar extensión
        if '.' not in archivo.filename:
            return False, "El archivo debe tener una extensión válida"
        
        extension = '.' + archivo.filename.lower().split('.')[-1]
        if extension not in CertificacionValidator.EXTENSIONES_PERMITIDAS:
            return False, f"Tipo de archivo no permitido. Use: {', '.join(CertificacionValidator.EXTENSIONES_PERMITIDAS)}"
        
        # Validar tamaño usando content_length si está disponible
        if hasattr(archivo, 'content_length') and archivo.content_length:
            if archivo.content_length > CertificacionValidator.TAMAÑO_MAXIMO:
                tamaño_mb = round(archivo.content_length / (1024 * 1024), 2)
                return False, f"El archivo ({tamaño_mb}MB) excede el tamaño máximo de 5MB"
        
        # Validar tamaño leyendo el archivo temporalmente
        try:
            archivo.seek(0, 2)  # Ir al final del archivo
            tamaño = archivo.tell()
            archivo.seek(0)  # Volver al inicio
            
            if tamaño > CertificacionValidator.TAMAÑO_MAXIMO:
                tamaño_mb = round(tamaño / (1024 * 1024), 2)
                return False, f"El archivo ({tamaño_mb}MB) excede el tamaño máximo de 5MB"
        except:
            pass  # Si no se puede verificar el tamaño, continuar
        
        return True, "Archivo válido"
    
    @staticmethod
    def validar_certificaciones_requeridas(archivos):
        """Valida que se proporcionen certificaciones sanitarias obligatorias"""
        if not archivos or len(archivos) == 0:
            return False, "Debe adjuntar al menos una certificación sanitaria"
        
        return True, "Certificaciones válidas"