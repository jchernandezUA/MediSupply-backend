from typing import Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from app.models import db
from app.models.plan_venta import PlanVenta
from app.models.vendedor import Vendedor
from . import NotFoundError, ConflictError, ValidationError

def _to_dict(p: PlanVenta) -> Dict[str, Any]:
    return {
        "id": p.id,
        "vendedorId": p.vendedor_id,
        "periodo": p.periodo,
        "objetivoMensual": float(p.objetivo_mensual),
        "metaUnidades": p.meta_unidades,
        "estado": p.estado,
        "fechaCreacion": p.fecha_creacion.isoformat() if p.fecha_creacion else None,
        "fechaActualizacion": p.fecha_actualizacion.isoformat() if p.fecha_actualizacion else None,
    }

def crear_o_actualizar_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ("vendedorId", "periodo", "objetivoMensual")
    if any(k not in payload for k in required):
        raise ValidationError("vendedorId, periodo y objetivoMensual son obligatorios")

    vend = Vendedor.query.get(payload["vendedorId"])
    if not vend:
        raise NotFoundError("vendedor no encontrado")

    plan = (
        PlanVenta.query
        .filter(PlanVenta.vendedor_id == payload["vendedorId"], PlanVenta.periodo == payload["periodo"])
        .one_or_none()
    )

    if plan:
        plan.objetivo_mensual = payload["objetivoMensual"]
        plan.meta_unidades = payload.get("metaUnidades")
        plan.estado = payload.get("estado", plan.estado)
    else:
        plan = PlanVenta(
            id=str(uuid4()),
            vendedor_id=payload["vendedorId"],
            periodo=payload["periodo"],  # YYYY-MM
            objetivo_mensual=payload["objetivoMensual"],
            meta_unidades=payload.get("metaUnidades"),
            estado=payload.get("estado", "activo"),
        )
        db.session.add(plan)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Podría ser la unique (vendedor_id, periodo)
        raise ConflictError("ya existe un plan para ese vendedor y periodo")

    return _to_dict(plan)

def listar_planes(
    vendedor_id: Optional[str] = None,
    periodo: Optional[str] = None,
    page: int = 1,
    size: int = 10,
) -> Dict[str, Any]:
    q = PlanVenta.query
    if vendedor_id:
        q = q.filter(PlanVenta.vendedor_id == vendedor_id)
    if periodo:
        q = q.filter(PlanVenta.periodo == periodo)

    total = q.count()
    items: List[PlanVenta] = (
        q.order_by(PlanVenta.fecha_creacion.desc())
         .offset((page - 1) * size)
         .limit(size)
         .all()
    )
    return {
        "items": [_to_dict(p) for p in items],
        "page": page,
        "size": size,
        "total": total,
    }
