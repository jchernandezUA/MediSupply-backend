"""
Modelo para trackear jobs de importación asíncrona
"""
from app.extensions import db
from datetime import datetime
import uuid


class ImportJob(db.Model):
    """
    Modelo para trackear jobs de importación de productos
    Permite monitorear el estado y progreso de importaciones masivas
    """
    
    __tablename__ = 'import_jobs'
    
    # Identificación
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre_archivo = db.Column(db.String(255), nullable=False)
    
    # S3
    s3_key = db.Column(db.String(500), nullable=True)  # Ruta del archivo en S3
    s3_bucket = db.Column(db.String(100), nullable=True)
    
    # Estado del job
    estado = db.Column(db.String(20), default='PENDIENTE', nullable=False)
    # Estados posibles: PENDIENTE, EN_COLA, PROCESANDO, COMPLETADO, FALLIDO, CANCELADO
    
    # Progreso
    total_filas = db.Column(db.Integer, default=0)
    filas_procesadas = db.Column(db.Integer, default=0)
    exitosos = db.Column(db.Integer, default=0)
    fallidos = db.Column(db.Integer, default=0)
    progreso = db.Column(db.Float, default=0.0)  # Porcentaje 0-100
    
    # Mensajes y errores
    mensaje_error = db.Column(db.Text, nullable=True)
    detalles_errores = db.Column(db.JSON, nullable=True)
    
    # SQS
    sqs_message_id = db.Column(db.String(100), nullable=True)
    sqs_receipt_handle = db.Column(db.String(500), nullable=True)
    reintentos = db.Column(db.Integer, default=0)
    
    # Auditoría
    usuario_registro = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_inicio_proceso = db.Column(db.DateTime, nullable=True)
    fecha_finalizacion = db.Column(db.DateTime, nullable=True)
    
    # Metadata adicional (nota: 'metadata' está reservado por SQLAlchemy)
    extra_metadata = db.Column(db.JSON, nullable=True)  # Para almacenar info adicional
    
    def __repr__(self):
        return f"<ImportJob {self.id} - {self.estado}>"
    
    def to_dict(self, include_errors=True):
        """
        Serializa el job a diccionario
        
        Args:
            include_errors: Si incluir detalles de errores completos
            
        Returns:
            dict: Representación del job
        """
        data = {
            'job_id': self.id,
            'nombre_archivo': self.nombre_archivo,
            'estado': self.estado,
            'progreso': round(self.progreso, 2),
            'total_filas': self.total_filas,
            'filas_procesadas': self.filas_procesadas,
            'exitosos': self.exitosos,
            'fallidos': self.fallidos,
            'usuario_registro': self.usuario_registro,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_inicio_proceso': self.fecha_inicio_proceso.isoformat() if self.fecha_inicio_proceso else None,
            'fecha_finalizacion': self.fecha_finalizacion.isoformat() if self.fecha_finalizacion else None,
            'tiempo_transcurrido_segundos': self._calcular_tiempo_transcurrido(),
            'reintentos': self.reintentos
        }
        
        # Agregar mensaje de error si existe
        if self.mensaje_error:
            data['mensaje_error'] = self.mensaje_error
        
        # Agregar detalles de errores si se solicita y existen
        if include_errors and self.detalles_errores:
            # Limitar cantidad de errores retornados para no sobrecargar respuesta
            max_errores = 10
            if isinstance(self.detalles_errores, list):
                data['detalles_errores'] = self.detalles_errores[:max_errores]
                if len(self.detalles_errores) > max_errores:
                    data['total_errores'] = len(self.detalles_errores)
                    data['nota'] = f'Mostrando {max_errores} de {len(self.detalles_errores)} errores'
            else:
                data['detalles_errores'] = self.detalles_errores
        
        return data
    
    def _calcular_tiempo_transcurrido(self):
        """
        Calcula tiempo transcurrido en segundos
        
        Returns:
            int: Segundos transcurridos o None si no ha iniciado
        """
        if not self.fecha_inicio_proceso:
            return None
        
        fin = self.fecha_finalizacion or datetime.utcnow()
        delta = fin - self.fecha_inicio_proceso
        return int(delta.total_seconds())
    
    def actualizar_progreso(self, filas_procesadas, exitosos, fallidos):
        """
        Actualiza el progreso del job
        
        Args:
            filas_procesadas: Número de filas procesadas
            exitosos: Número de productos creados exitosamente
            fallidos: Número de productos que fallaron
        """
        self.filas_procesadas = filas_procesadas
        self.exitosos = exitosos
        self.fallidos = fallidos
        
        if self.total_filas > 0:
            self.progreso = (filas_procesadas / self.total_filas) * 100
        else:
            self.progreso = 0
    
    def marcar_como_procesando(self):
        """Marca el job como en procesamiento"""
        self.estado = 'PROCESANDO'
        self.fecha_inicio_proceso = datetime.utcnow()
    
    def marcar_como_completado(self, mensaje=None):
        """
        Marca el job como completado
        
        Args:
            mensaje: Mensaje adicional (opcional)
        """
        self.estado = 'COMPLETADO'
        self.progreso = 100.0
        self.fecha_finalizacion = datetime.utcnow()
        if mensaje:
            self.extra_metadata = self.extra_metadata or {}
            self.extra_metadata['mensaje_finalizacion'] = mensaje
    
    def marcar_como_fallido(self, error_mensaje):
        """
        Marca el job como fallido
        
        Args:
            error_mensaje: Mensaje de error
        """
        self.estado = 'FALLIDO'
        self.mensaje_error = error_mensaje
        self.fecha_finalizacion = datetime.utcnow()
    
    def es_terminal(self):
        """
        Verifica si el job está en un estado terminal
        
        Returns:
            bool: True si está completado, fallido o cancelado
        """
        return self.estado in ['COMPLETADO', 'FALLIDO', 'CANCELADO']
    
    def puede_reintentar(self, max_reintentos=2):
        """
        Verifica si el job puede reintentarse
        
        Args:
            max_reintentos: Máximo de reintentos permitidos
            
        Returns:
            bool: True si puede reintentarse
        """
        return self.estado == 'FALLIDO' and self.reintentos < max_reintentos
