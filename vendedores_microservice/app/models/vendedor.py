from . import db

class Vendedor(db.Model):
    __tablename__ = "vendedores"

    id = db.Column(db.String(36), primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    apellidos = db.Column(db.String(150), nullable=False)
    correo = db.Column(db.String(255), nullable=False, unique=True, index=True)
    celular = db.Column(db.String(20), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    zona = db.Column(db.String(80), nullable=True)  # País o zona de asignación (opcional)
    estado = db.Column(db.String(20), nullable=False, default="activo")
    
    # Auditoría
    usuario_creacion = db.Column(db.String(100), nullable=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    usuario_actualizacion = db.Column(db.String(100), nullable=True)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    planes = db.relationship("PlanVenta", back_populates="vendedor", cascade="all, delete-orphan", lazy="selectin")
    asignaciones = db.relationship("AsignacionZona", back_populates="vendedor", cascade="all, delete-orphan", lazy="selectin")
