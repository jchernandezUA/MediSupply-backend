from app.extensions import db
from datetime import datetime

# Categorías fijas según HU KAN-96
CATEGORIAS_VALIDAS = ['medicamento', 'insumo', 'reactivo', 'dispositivo']

class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    codigo_sku = db.Column(db.String(50), unique=True, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  # medicamento, insumo, reactivo, dispositivo
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # Precio en USD
    condiciones_almacenamiento = db.Column(db.Text, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='Activo')  # Activo o Inactivo
    
    # Auditoría
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    usuario_registro = db.Column(db.String(120), nullable=False)  # Usuario que creó el producto
    
    # Relación con proveedor (FK al microservicio de proveedores)
    proveedor_id = db.Column(db.Integer, nullable=False)  # ID del proveedor desde otro microservicio
    
    # Relación con certificación (uno a uno)
    certificacion = db.relationship('CertificacionProducto', backref='producto', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Producto {self.nombre} - SKU: {self.codigo_sku}>"
    
    def esta_activo(self):
        """Verifica si el producto está activo"""
        return self.estado == 'Activo'
    
    def activar(self):
        """Activa el producto"""
        self.estado = 'Activo'
    
    def desactivar(self):
        """Desactiva el producto"""
        self.estado = 'Inactivo'
    
    def tiene_certificacion_valida(self):
        """Verifica si el producto tiene certificación válida"""
        return self.certificacion is not None


class CertificacionProducto(db.Model):
    __tablename__ = "certificaciones_producto"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    
    tipo_certificacion = db.Column(db.String(50), nullable=False)  # INVIMA, FDA, EMA
    nombre_archivo = db.Column(db.String(255), nullable=False)
    ruta_archivo = db.Column(db.String(500), nullable=False)
    tamaño_archivo = db.Column(db.Integer)  # Tamaño en bytes
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_vencimiento_cert = db.Column(db.Date, nullable=False)  # Fecha vencimiento de la certificación

    def __repr__(self):
        return f"<CertificacionProducto {self.tipo_certificacion} - {self.nombre_archivo}>"
