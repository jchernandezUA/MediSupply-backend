from typing import Optional, Dict, Any, List
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from app.models import db
from app.models.vendedor import Vendedor
from app.utils.validators import require, is_valid_email, is_valid_phone, length_between
from . import NotFoundError, ConflictError, ValidationError

def _to_dict(v: Vendedor) -> Dict[str, Any]:
    """Convierte un vendedor a diccionario para la respuesta JSON."""
    return {
        "id": v.id,
        "nombre": v.nombre,
        "apellidos": v.apellidos,
        "correo": v.correo,
        "telefono": v.telefono,
        "zona": v.zona,
        "estado": v.estado,
        "usuarioCreacion": v.usuario_creacion,
        "fechaCreacion": v.fecha_creacion.isoformat() if v.fecha_creacion else None,
        "usuarioActualizacion": v.usuario_actualizacion,
        "fechaActualizacion": v.fecha_actualizacion.isoformat() if v.fecha_actualizacion else None,
    }

def crear_vendedor(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea un nuevo vendedor con validaciones completas según HU KAN-83.
    
    Validaciones:
    - Campos obligatorios: nombre, apellidos, correo, telefono
    - Formato de correo válido
    - Celular con mínimo 10 dígitos
    - Correo único (no duplicado)
    """
    # Validar campos obligatorios
    require(payload, ["nombre", "apellidos", "correo", "telefono"])
    
    # Validar formato de correo
    is_valid_email(payload["correo"])
    
    # Validar formato de celular (mínimo 10 dígitos)
    is_valid_phone(payload["telefono"], field_name="telefono", min_length=10)
    
    # Validar longitud de campos
    length_between(payload["nombre"], 1, 150, "nombre")
    length_between(payload["apellidos"], 1, 150, "apellidos")
    length_between(payload["correo"], 5, 255, "correo")
    length_between(payload["telefono"], 10, 20, "telefono")
    
    # Validar zona si se proporciona
    if payload.get("zona"):
        length_between(payload["zona"], 1, 80, "zona")
    
    # Verificar si ya existe un vendedor con el mismo correo
    vendedor_existente = Vendedor.query.filter_by(correo=payload["correo"]).first()
    if vendedor_existente:
        raise ConflictError("Ya existe un vendedor registrado con ese correo electrónico")
    
    # Crear el vendedor
    vendedor = Vendedor(
        id=payload.get("id") or str(uuid4()),
        nombre=payload["nombre"],
        apellidos=payload["apellidos"],
        correo=payload["correo"].lower().strip(),  # Normalizar correo
        telefono=payload.get("telefono"),
        zona=payload.get("zona"),
        estado=payload.get("estado", "activo"),
        usuario_creacion=payload.get("usuario_creacion", "sistema"),
    )
    
    db.session.add(vendedor)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al crear vendedor: {str(e)}")
        # Por si acaso hay algún problema de concurrencia
        raise ConflictError(f"Ya existe un vendedor registrado con ese correo electrónico, error: {str(e)}")
    
    return _to_dict(vendedor)

def obtener_vendedor(v_id: str) -> Dict[str, Any]:
    """Obtiene un vendedor por su ID."""
    v = Vendedor.query.get(v_id)
    if not v:
        raise NotFoundError("vendedor no encontrado")
    return _to_dict(v)

def actualizar_vendedor(v_id: str, cambios: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza un vendedor existente.
    
    Validaciones:
    - Vendedor debe existir
    - Si se actualiza el correo, validar formato y que no esté duplicado
    - Si se actualiza el celular, validar longitud mínima
    """
    v = Vendedor.query.get(v_id)
    if not v:
        raise NotFoundError("vendedor no encontrado")

    # Validar campos si están presentes
    if "nombre" in cambios:
        if not cambios["nombre"]:
            raise ValidationError("nombre no puede ser vacío")
        length_between(cambios["nombre"], 1, 150, "nombre")
    
    if "apellidos" in cambios:
        if not cambios["apellidos"]:
            raise ValidationError("apellidos no puede ser vacío")
        length_between(cambios["apellidos"], 1, 150, "apellidos")
    
    if "correo" in cambios:
        is_valid_email(cambios["correo"])
        length_between(cambios["correo"], 5, 255, "correo")
        
        # Verificar que no esté duplicado (excepto el mismo vendedor)
        correo_normalizado = cambios["correo"].lower().strip()
        vendedor_existente = Vendedor.query.filter(
            Vendedor.correo == correo_normalizado,
            Vendedor.id != v_id
        ).first()
        if vendedor_existente:
            raise ConflictError("Ya existe un vendedor registrado con ese correo electrónico")
        
        cambios["correo"] = correo_normalizado
    
    if "celular" in cambios:
        is_valid_phone(cambios["celular"], field_name="celular", min_length=10)
        length_between(cambios["celular"], 10, 20, "celular")
    
    if "telefono" in cambios and cambios["telefono"]:
        is_valid_phone(cambios["telefono"], field_name="telefono", min_length=10)
        length_between(cambios["telefono"], 10, 20, "telefono")
    
    if "zona" in cambios and cambios["zona"]:
        length_between(cambios["zona"], 1, 80, "zona")

    # Actualizar campos permitidos
    for field in ("nombre", "apellidos", "correo", "celular", "telefono", "zona", "estado"):
        if field in cambios:
            setattr(v, field, cambios[field])
    
    # Actualizar auditoría
    if "usuario_actualizacion" in cambios:
        v.usuario_actualizacion = cambios["usuario_actualizacion"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("Ya existe un vendedor registrado con ese correo electrónico")
    
    return _to_dict(v)

def listar_vendedores(
    zona: Optional[str] = None,
    estado: Optional[str] = None,
    page: int = 1,
    size: int = 10,
) -> Dict[str, Any]:
    """Lista vendedores con paginación y filtros opcionales."""
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
