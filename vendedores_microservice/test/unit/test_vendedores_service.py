import pytest
from app.models import db
from app.services.vendedores_service import (
    crear_vendedor, obtener_vendedor, actualizar_vendedor, listar_vendedores
)
from app.utils.errors import ValidationError, ConflictError, NotFoundError

def test_crear_y_obtener_vendedor(app_ctx):
    """Prueba crear un vendedor con todos los campos obligatorios según HU KAN-83."""
    out = crear_vendedor({
        "nombre": "Juan",
        "apellidos": "Pérez García",
        "correo": "juan.perez@example.com",
        "telefono": "6015551234",
        "zona": "Norte"
    })
    assert out["nombre"] == "Juan"
    assert out["apellidos"] == "Pérez García"
    assert out["correo"] == "juan.perez@example.com"
    assert out["telefono"] == "6015551234"
    
    got = obtener_vendedor(out["id"])
    assert got["nombre"] == "Juan"
    assert got["zona"] == "Norte"

def test_correo_unico(app_ctx):
    """Verifica que no se puedan registrar dos vendedores con el mismo correo (duplicados)."""
    crear_vendedor({
        "nombre": "Ana",
        "apellidos": "López",
        "correo": "ana@example.com",
        "telefono": "3001111111"
    })
    
    with pytest.raises(ConflictError, match="Ya existe un vendedor registrado con ese correo"):
        crear_vendedor({
            "nombre": "María",
            "apellidos": "González",
            "correo": "ana@example.com",  # Correo duplicado
            "telefono": "3002222222"
        })

def test_validacion_correo_formato_invalido(app_ctx):
    """Valida que se rechace un correo con formato inválido."""
    with pytest.raises(ValidationError, match="formato válido"):
        crear_vendedor({
            "nombre": "Pedro",
            "apellidos": "Ramírez",
            "correo": "correo-invalido",  # Sin @ y dominio
            "telefono": "3003333333"
        })

def test_validacion_telefono_minimo_10_digitos(app_ctx):
    """Valida que el telefono tenga mínimo 10 dígitos."""
    with pytest.raises(ValidationError, match="debe tener al menos 10 dígitos"):
        crear_vendedor({
            "nombre": "Carlos",
            "apellidos": "Martínez",
            "correo": "carlos@example.com",
            "telefono": "123"  # Muy corto
        })

def test_validaciones_campos_obligatorios(app_ctx):
    """Valida que todos los campos obligatorios estén presentes."""
    # Falta nombre
    with pytest.raises(ValidationError, match="Faltan campos obligatorios"):
        crear_vendedor({
            "apellidos": "González",
            "correo": "test@example.com",
            "telefono": "3001234567"
        })
    
    # Falta apellidos
    with pytest.raises(ValidationError, match="Faltan campos obligatorios"):
        crear_vendedor({
            "nombre": "Test",
            "correo": "test@example.com",
            "telefono": "3001234567"
        })
    
    # Falta correo
    with pytest.raises(ValidationError, match="Faltan campos obligatorios"):
        crear_vendedor({
            "nombre": "Test",
            "apellidos": "User",
            "telefono": "3001234567"
        })
    
    # Falta telefono
    with pytest.raises(ValidationError, match="Faltan campos obligatorios"):
        crear_vendedor({
            "nombre": "Test",
            "apellidos": "User",
            "correo": "test@example.com"
        })

def test_zona_opcional(app_ctx):
    """Verifica que el campo zona sea opcional."""
    out = crear_vendedor({
        "nombre": "Luis",
        "apellidos": "Hernández",
        "correo": "luis@example.com",
        "telefono": "3004444444"
        # zona no proporcionada
    })
    assert out["zona"] is None

def test_actualizar_vendedor(app_ctx):
    """Prueba actualizar los datos de un vendedor."""
    v = crear_vendedor({
        "nombre": "Roberto",
        "apellidos": "Gómez",
        "correo": "roberto@example.com",
        "telefono": "3006666666",
        "zona": "Norte"
    })
    
    updated = actualizar_vendedor(v["id"], {
        "nombre": "Roberto Carlos",
        "zona": "Centro",
        "usuario_actualizacion": "admin"
    })
    
    assert updated["nombre"] == "Roberto Carlos"
    assert updated["zona"] == "Centro"
    assert updated["apellidos"] == "Gómez"  # No cambió
    assert updated["usuarioActualizacion"] == "admin"

def test_actualizar_correo_no_duplicado(app_ctx):
    """Verifica que no se pueda actualizar el correo a uno que ya existe."""
    crear_vendedor({
        "nombre": "User1",
        "apellidos": "Test",
        "correo": "user1@example.com",
        "telefono": "3001111111"
    })
    
    v2 = crear_vendedor({
        "nombre": "User2",
        "apellidos": "Test",
        "correo": "user2@example.com",
        "telefono": "3002222222"
    })
    
    with pytest.raises(ConflictError, match="Ya existe un vendedor registrado con ese correo"):
        actualizar_vendedor(v2["id"], {"correo": "user1@example.com"})

def test_listar_vendedores_con_filtros(app_ctx):
    """Prueba listar vendedores con filtros de zona y estado."""
    crear_vendedor({
        "nombre": "V1",
        "apellidos": "Test",
        "correo": "v1@example.com",
        "telefono": "3001111111",
        "zona": "Norte",
        "estado": "activo"
    })
    
    crear_vendedor({
        "nombre": "V2",
        "apellidos": "Test",
        "correo": "v2@example.com",
        "telefono": "3002222222",
        "zona": "Centro",
        "estado": "activo"
    })
    
    listado = listar_vendedores(zona="Norte", estado="activo", page=1, size=10)
    assert listado["total"] == 1
    assert listado["items"][0]["zona"] == "Norte"

def test_vendedor_no_encontrado(app_ctx):
    """Verifica que se lance NotFoundError si el vendedor no existe."""
    with pytest.raises(NotFoundError, match="vendedor no encontrado"):
        obtener_vendedor("id-inexistente")
    
    with pytest.raises(NotFoundError, match="vendedor no encontrado"):
        actualizar_vendedor("id-inexistente", {"nombre": "Test"})

def test_auditoria_creacion(app_ctx):
    """Verifica que se guarde la información de auditoría al crear."""
    out = crear_vendedor({
        "nombre": "Audit",
        "apellidos": "Test",
        "correo": "audit@example.com",
        "telefono": "3009999999",
        "usuario_creacion": "admin@system.com"
    })
    
    assert out["usuarioCreacion"] == "admin@system.com"
    assert out["fechaCreacion"] is not None

