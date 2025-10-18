import re
from datetime import date
from uuid import UUID
from .errors import ValidationError


def require(payload: dict, fields: list[str]) -> None:
    """Exige que existan y no sean vacíos (None/''/[]) los campos indicados."""
    missing = [f for f in fields if payload.get(f) in (None, "", [])]
    if missing:
        raise ValidationError(f"Faltan campos obligatorios: {', '.join(missing)}")


def ensure_types(payload: dict, schema: dict[str, tuple | type]) -> None:
    """
    Verifica tipos por campo. schema: {'campo': (int, float)} o {'campo': str}
    Solo valida si el campo existe (permite opcionales).
    """
    for field, expected in schema.items():
        if field in payload and payload[field] is not None:
            if not isinstance(payload[field], expected if isinstance(expected, tuple) else (expected,)):
                tn = expected if isinstance(expected, tuple) else (expected,)
                names = ", ".join(t.__name__ for t in tn)
                raise ValidationError(f"Tipo inválido para '{field}', se esperaba: {names}")


def one_of(value, allowed: list, field_name: str) -> None:
    """Valida que value ∈ allowed."""
    if value not in allowed:
        raise ValidationError(f"'{field_name}' debe ser uno de: {', '.join(map(str, allowed))}")


def length_between(value: str, min_len: int, max_len: int, field_name: str) -> None:
    """Valida longitud mínima y máxima para strings."""
    if value is None:
        return
    n = len(value)
    if n < min_len or n > max_len:
        raise ValidationError(f"'{field_name}' debe tener entre {min_len} y {max_len} caracteres")


def matches_regex(value: str, pattern: str, field_name: str, flags: int = 0) -> None:
    """Valida un patrón regex."""
    if value is None:
        return
    if re.fullmatch(pattern, value, flags) is None:
        raise ValidationError(f"'{field_name}' tiene un formato inválido")


def is_uuid(value: str, field_name: str) -> None:
    """Valida que sea UUID v4/v5/etc (formato estándar)."""
    if value is None:
        return
    try:
        UUID(str(value))
    except Exception:
        raise ValidationError(f"'{field_name}' no es un UUID válido")


_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")  # YYYY-MM


def is_period(value: str, field_name: str) -> None:
    """Valida periodo 'YYYY-MM'."""
    if value is None:
        return
    if _PERIOD_RE.fullmatch(value) is None:
        raise ValidationError(f"'{field_name}' debe tener formato YYYY-MM")


def is_date(value: str, field_name: str) -> None:
    """Valida fecha ISO 'YYYY-MM-DD'."""
    if value is None:
        return
    try:
        date.fromisoformat(value)
    except Exception:
        raise ValidationError(f"'{field_name}' debe tener formato YYYY-MM-DD")


def positive_int(value, field_name: str) -> None:
    """Valida entero positivo."""
    if value is None:
        return
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"'{field_name}' debe ser un entero positivo")


def pagination_params(page, size, max_size: int = 100) -> tuple[int, int]:
    """
    Normaliza y valida paginación.
    - page: entero ≥ 1
    - size: entero entre 1 y max_size
    """
    try:
        p = int(page)
        s = int(size)
    except Exception:
        raise ValidationError("page y size deben ser enteros")

    if p < 1:
        raise ValidationError("page debe ser ≥ 1")
    if s < 1 or s > max_size:
        raise ValidationError(f"size debe estar entre 1 y {max_size}")
    return p, s


def is_valid_email(email: str, field_name: str = "correo") -> None:
    """
    Valida que el correo electrónico tenga un formato válido.
    Patrón: texto@dominio.extension
    """
    if not email:
        raise ValidationError(f"'{field_name}' es obligatorio")
    
    # Patrón de email simplificado pero efectivo
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError(f"'{field_name}' no tiene un formato válido")


def is_valid_phone(phone: str, field_name: str = "celular", min_length: int = 10) -> None:
    """
    Valida que el número de teléfono/celular tenga al menos min_length dígitos.
    Permite espacios, guiones y paréntesis, pero debe tener al menos 10 dígitos.
    """
    if not phone:
        raise ValidationError(f"'{field_name}' es obligatorio")
    
    # Extraer solo los dígitos
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) < min_length:
        raise ValidationError(f"'{field_name}' debe tener al menos {min_length} dígitos")
