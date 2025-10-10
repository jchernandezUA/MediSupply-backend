from . import db

class Vendedor(db.Model):
    __tablename__ = "vendedores"

    id = db.Column(db.String(36), primary_key=True)
    identificacion = db.Column(db.String(30), nullable=False, unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    zona = db.Column(db.String(80), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default="activo")
    fecha_creacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    planes = db.relationship("PlanVenta", back_populates="vendedor", cascade="all, delete-orphan", lazy="selectin")
    asignaciones = db.relationship("AsignacionZona", back_populates="vendedor", cascade="all, delete-orphan", lazy="selectin")
