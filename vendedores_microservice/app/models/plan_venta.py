from . import db

class PlanVenta(db.Model):
    __tablename__ = "planes_venta"

    id = db.Column(db.String(36), primary_key=True)
    vendedor_id = db.Column(db.String(36), db.ForeignKey("vendedores.id", ondelete="CASCADE"), nullable=False)
    periodo = db.Column(db.String(7), nullable=False)  # YYYY-MM
    objetivo_mensual = db.Column(db.Numeric(14, 2), nullable=False)
    meta_unidades = db.Column(db.Integer, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default="activo")
    fecha_creacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    vendedor = db.relationship("Vendedor", back_populates="planes")
    __table_args__ = (db.UniqueConstraint("vendedor_id", "periodo", name="uq_planes_venta_vendedor_periodo"),)
    def to_dict(self):
        return {
            "id": self.id,
            "vendedor_id": self.vendedor_id,
            "periodo": self.periodo,
            "objetivo_mensual": float(self.objetivo_mensual),
            "meta_unidades": self.meta_unidades,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "fecha_actualizacion": self.fecha_actualizacion.isoformat(),
        }