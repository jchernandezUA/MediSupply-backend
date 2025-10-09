from . import db

class AsignacionZona(db.Model):
    __tablename__ = "asignaciones_zona"

    id = db.Column(db.String(36), primary_key=True)
    vendedor_id = db.Column(db.String(36), db.ForeignKey("vendedores.id", ondelete="CASCADE"), nullable=False)
    zona = db.Column(db.String(80), nullable=False)
    fecha_asignacion = db.Column(db.Date, nullable=False)
    fecha_liberacion = db.Column(db.Date, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default="activo")
    fecha_creacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    vendedor = db.relationship("Vendedor", back_populates="asignaciones")
    
    def to_dict(self):
        return {
            "id": self.id,
            "vendedor_id": self.vendedor_id,
            "zona": self.zona,
            "fecha_asignacion": self.fecha_asignacion.isoformat() if self.fecha_asignacion else None,
            "fecha_liberacion": self.fecha_liberacion.isoformat() if self.fecha_liberacion else None,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "fecha_actualizacion": self.fecha_actualizacion.isoformat(),
        }