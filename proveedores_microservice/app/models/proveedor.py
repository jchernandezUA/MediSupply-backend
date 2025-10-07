from app.extensions import db
from datetime import datetime
import re

class Proveedor(db.Model):
    __tablename__ = "proveedores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    nit = db.Column(db.String(20), unique=True, nullable=False)
    pais = db.Column(db.String(60), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='Activo')  # 'Activo' o 'Inactivo'
    direccion = db.Column(db.String(200))
    nombre_contacto = db.Column(db.String(120))
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(30))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con certificaciones
    certificaciones = db.relationship('Certificacion', backref='proveedor', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Proveedor {self.nombre}>"
    
    def tiene_certificaciones_validas(self):
        """Verifica si el proveedor tiene certificaciones sanitarias válidas"""
        return len(self.certificaciones) > 0
    
    def activar(self):
        """Activa el proveedor"""
        self.estado = 'Activo'
    
    def desactivar(self):
        """Desactiva el proveedor"""
        self.estado = 'Inactivo'
    
    def esta_activo(self):
        """Verifica si el proveedor está activo"""
        return self.estado == 'Activo'


class Certificacion(db.Model):
    __tablename__ = "certificaciones"
    
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    ruta_archivo = db.Column(db.String(500), nullable=False)
    tipo_certificacion = db.Column(db.String(100), nullable=False)  # 'sanitaria', 'calidad', etc.
    tamaño_archivo = db.Column(db.Integer, nullable=False)  # en bytes
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Certificacion {self.nombre_archivo}>"
