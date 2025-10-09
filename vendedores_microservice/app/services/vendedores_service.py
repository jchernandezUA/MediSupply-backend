from typing import Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from app.models import db
from app.models.vendedor import Vendedor
from . import NotFoundError, ConflictError, ValidationError

def _to_dict(v: Vendedor) -> Dict[str, Any]:
    return {
        "id": v.id,
        "identificacion": v.identificacion,
        "nombre": v.nombre,
        "zona": v.zona,
        "estado": v.estado,
        "fechaCreacion": v.fecha_creacion.isoformat() if v.fecha_creacion else None,
        "fechaActualizacion": v.fecha_actualizacion.isoformat() if v.fecha_actualizacion else None,
    }

def crear_vendedor(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not payload.get("identificacion") or not payload.get("nombre"):
        raise ValidationError("identificacion y nombre son obligatorios")

    vendedor = Vendedor(
        id=payload.get("id") or str(uuid4()),
        identificacion=payload["identificacion"],
        nombre=payload["nombre"],
        zona=payload.get("zona"),
        estado=payload.get("estado", "activo"),
    )
    db.session.add(vendedor)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("identificacion ya registrada")
    return _to_dict(vendedor)

def obtener_vendedor(v_id: str) -> Dict[str, Any]:
    v = Vendedor.query.get(v_id)
    if not v:
        raise NotFoundError("vendedor no encontrado")
    return _to_dict(v)

def actualizar_vendedor(v_id: str, cambios: Dict[str, Any]) -> Dict[str, Any]:
    v = Vendedor.query.get(v_id)
    if not v:
        raise NotFoundError("vendedor no encontrado")

    if "identificacion" in cambios and not cambios["identificacion"]:
        raise ValidationError("identificacion no puede ser vacía")
    if "nombre" in cambios and not cambios["nombre"]:
        raise ValidationError("nombre no puede ser vacío")

    for field in ("identificacion", "nombre", "zona", "estado"):
        if field in cambios:
            setattr(v, field, cambios[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("identificacion ya registrada")
    return _to_dict(v)

def listar_vendedores(
    zona: Optional[str] = None,
    estado: Optional[str] = None,
    page: int = 1,
    size: int = 10,
) -> Dict[str, Any]:
    q = Vendedor.query
    if zona:
        q = q.filter(Vendedor.zona == zona)
    if estado:
        q = q.filter(Vendedor.estado == estado)

    total = q.count()
    items: List[Vendedor] = (
        q.order_by(Vendedor.fecha_creacion.desc())
         .offset((page - 1) * size)
         .limit(size)
         .all()
    )
    return {
        "items": [_to_dict(v) for v in items],
        "page": page,
        "size": size,
        "total": total,
    }
