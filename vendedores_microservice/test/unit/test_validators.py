import pytest
from app.utils.validators import (
    require, ensure_types, one_of, length_between, matches_regex,
    is_uuid, is_period, is_date, positive_int, pagination_params
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
