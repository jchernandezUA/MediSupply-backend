import pytest
from app.models import db
from app.services.vendedores_service import (
    crear_vendedor, obtener_vendedor, actualizar_vendedor, listar_vendedores
)
from app.utils.errors import ValidationError, ConflictError, NotFoundError

def test_crear_y_obtener_vendedor(app_ctx):
    out = crear_vendedor({"identificacion": "CC123", "nombre": "Ana", "zona": "Norte"})
    assert out["identificacion"] == "CC123"
    got = obtener_vendedor(out["id"])
    assert got["nombre"] == "Ana"

def test_identificacion_unica(app_ctx):
    crear_vendedor({"identificacion": "CC1", "nombre": "A"})
    with pytest.raises(ConflictError):
        crear_vendedor({"identificacion": "CC1", "nombre": "B"})

def test_validaciones_crear(app_ctx):
    with pytest.raises(ValidationError):
        crear_vendedor({"nombre": "SinId"})
    with pytest.raises(ValidationError):
        crear_vendedor({"identificacion": "X"})

def test_actualizar_y_listar(app_ctx):
    v = crear_vendedor({"identificacion": "CC9", "nombre": "Ana", "zona": "Norte", "estado": "activo"})
    updated = actualizar_vendedor(v["id"], {"nombre": "Ana María", "zona": "Centro"})
    assert updated["nombre"] == "Ana María"
    listado = listar_vendedores(zona="Centro", estado="activo", page=1, size=10)
    assert listado["total"] == 1
    with pytest.raises(NotFoundError):
        actualizar_vendedor("no-existe", {"nombre": "X"})
