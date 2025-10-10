from typing import Optional, Dict, Any, List
from uuid import uuid4
from app.models import db
from app.models.asignacion import AsignacionZona
from app.models.vendedor import Vendedor
from . import NotFoundError, ValidationError

def _to_dict(a: AsignacionZona) -> Dict[str, Any]:
    return {
        "id": a.id,
        "vendedorId": a.vendedor_id,
        "zona": a.zona,
        "vigenteDesde": a.vigente_desde.isoformat() if a.vigente_desde else None,
        "vigenteHasta": a.vigente_hasta.isoformat() if a.vigente_hasta else None,
        "activa": a.activa,
        "fechaCreacion": a.fecha_creacion.isoformat() if a.fecha_creacion else None,
        "fechaActualizacion": a.fecha_actualizacion.isoformat() if a.fecha_actualizacion else None,
    }

def crear_asignacion(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ("vendedorId", "zona", "vigenteDesde")
    if any(k not in payload for k in required):
        raise ValidationError("vendedorId, zona y vigenteDesde son obligatorios")

    vend = Vendedor.query.get(payload["vendedorId"])
    if not vend:
        raise NotFoundError("vendedor no encontrado")

    asign = AsignacionZona(
        id=str(uuid4()),
        vendedor_id=payload["vendedorId"],
        zona=payload["zona"],
        vigente_desde=payload["vigenteDesde"],
        vigente_hasta=payload.get("vigenteHasta"),
        activa=payload.get("activa", True),
    )
    db.session.add(asign)
    db.session.commit()
    return _to_dict(asign)

def cerrar_asignacion(asign_id: str, hasta_fecha) -> Dict[str, Any]:
    asign = AsignacionZona.query.get(asign_id)
    if not asign:
        raise NotFoundError("asignación no encontrada")
    asign.vigente_hasta = hasta_fecha
    asign.activa = False
    db.session.commit()
    return _to_dict(asign)

def listar_asignaciones(
    vendedor_id: Optional[str] = None,
    zona: Optional[str] = None,
    activas: Optional[bool] = None,
    page: int = 1,
    size: int = 10,
) -> Dict[str, Any]:
    q = AsignacionZona.query
    if vendedor_id:
        q = q.filter(AsignacionZona.vendedor_id == vendedor_id)
    if zona:
        q = q.filter(AsignacionZona.zona == zona)
    if activas is not None:
        q = q.filter(AsignacionZona.activa == bool(activas))

    total = q.count()
    items: List[AsignacionZona] = (
        q.order_by(AsignacionZona.fecha_creacion.desc())
         .offset((page - 1) * size)
         .limit(size)
         .all()
    )
    return {
        "items": [_to_dict(a) for a in items],
        "page": page,
        "size": size,
        "total": total,
    }
