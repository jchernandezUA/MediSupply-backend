import pytest
from app.utils.validators import (
    require, ensure_types, one_of, length_between, matches_regex,
    is_uuid, is_period, is_date, positive_int, pagination_params,
    is_valid_email, is_valid_phone
)
from app.utils.errors import ValidationError

def test_require_ok():
    require({"a": 1, "b": "x"}, ["a", "b"])

def test_require_falta():
    with pytest.raises(ValidationError):
        require({"a": 1}, ["a", "b"])

def test_ensure_types_ok():
    ensure_types({"a": 1, "b": "x"}, {"a": int, "b": (str, bytes)})

def test_ensure_types_fail():
    with pytest.raises(ValidationError):
        ensure_types({"a": "1"}, {"a": int})

def test_one_of():
    one_of("activo", ["activo", "inactivo"], "estado")
    with pytest.raises(ValidationError):
        one_of("otro", ["activo", "inactivo"], "estado")

def test_length_between():
    length_between("hola", 2, 10, "nombre")
    with pytest.raises(ValidationError):
        length_between("h", 2, 10, "nombre")

def test_matches_regex():
    matches_regex("ABC123", r"[A-Z0-9]+", "codigo")
    with pytest.raises(ValidationError):
        matches_regex("abc-123", r"[A-Z0-9]+", "codigo")

def test_is_uuid_y_periodo_y_fecha():
    is_uuid("123e4567-e89b-12d3-a456-426614174000", "id")
    is_period("2025-10", "periodo")
    is_date("2025-10-07", "fecha")
    with pytest.raises(ValidationError):
        is_period("2025-13", "periodo")

def test_positive_int_y_pagination():
    positive_int(5, "page")
    with pytest.raises(ValidationError):
        positive_int(0, "page")
    p, s = pagination_params(2, 10)
    assert (p, s) == (2, 10)
    with pytest.raises(ValidationError):
        pagination_params("x", 10)

def test_is_valid_email_correcto():
    """Prueba validación de correos válidos."""
    is_valid_email("usuario@example.com")
    is_valid_email("test.user@domain.co")
    is_valid_email("user+tag@company.com")
    is_valid_email("admin@sub.domain.org")

def test_is_valid_email_incorrecto():
    """Prueba validación de correos inválidos."""
    with pytest.raises(ValidationError, match="formato válido"):
        is_valid_email("sin-arroba.com")
    
    with pytest.raises(ValidationError, match="formato válido"):
        is_valid_email("@sinusuario.com")
    
    with pytest.raises(ValidationError, match="formato válido"):
        is_valid_email("usuario@")
    
    with pytest.raises(ValidationError, match="formato válido"):
        is_valid_email("usuario@dominio")
    
    with pytest.raises(ValidationError, match="obligatorio"):
        is_valid_email("")

def test_is_valid_phone_correcto():
    """Prueba validación de teléfonos válidos."""
    is_valid_phone("3001234567")  # 10 dígitos
    is_valid_phone("300-123-4567")  # Con guiones
    is_valid_phone("(300) 123-4567")  # Con paréntesis
    is_valid_phone("300 123 4567")  # Con espacios
    is_valid_phone("12345678901")  # 11 dígitos

def test_is_valid_phone_incorrecto():
    """Prueba validación de teléfonos inválidos."""
    with pytest.raises(ValidationError, match="debe tener al menos 10 dígitos"):
        is_valid_phone("123")  # Muy corto
    
    with pytest.raises(ValidationError, match="debe tener al menos 10 dígitos"):
        is_valid_phone("123456789")  # 9 dígitos
    
    with pytest.raises(ValidationError, match="obligatorio"):
        is_valid_phone("")
    
    with pytest.raises(ValidationError, match="obligatorio"):
        is_valid_phone(None)

def test_is_valid_phone_con_min_length_personalizado():
    """Prueba validación de teléfono con longitud mínima personalizada."""
    is_valid_phone("12345678", field_name="telefono", min_length=8)
    
    with pytest.raises(ValidationError, match="debe tener al menos 12 dígitos"):
        is_valid_phone("12345678901", field_name="telefono", min_length=12)

