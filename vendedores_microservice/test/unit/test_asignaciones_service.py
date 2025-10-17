from datetime import date
import pytest
from app.services.vendedores_service import crear_vendedor
from app.services.asignaciones_service import crear_asignacion, cerrar_asignacion, listar_asignaciones
from app.utils.errors import ValidationError, NotFoundError


def test_asignar_y_cerrar(app_ctx):
    """Test completo de crear y cerrar asignación"""
    # Crear vendedor con todos los campos obligatorios según HU KAN-83
    v = crear_vendedor({
        "nombre": "Luisa",
        "apellidos": "Martínez",
        "correo": "luisa.martinez@example.com",
        "celular": "3001234567"
    })
    a = crear_asignacion({"vendedorId": v["id"], "zona": "Occidente", "vigenteDesde": date(2025, 10, 1)})
    assert a["activa"] is True
    assert a["zona"] == "Occidente"
    assert a["vendedorId"] == v["id"]
    
    cerrada = cerrar_asignacion(a["id"], date(2025, 10, 7))
    assert cerrada["activa"] is False
    assert cerrada["vigenteHasta"] == "2025-10-07"
    
    lista = listar_asignaciones(vendedor_id=v["id"], activas=False)
    assert lista["total"] == 1 and lista["items"][0]["zona"] == "Occidente"


def test_crear_asignacion_campos_obligatorios(app_ctx):
    """Test que valida campos obligatorios en crear_asignacion"""
    # Sin vendedorId
    with pytest.raises(ValidationError, match="vendedorId, zona y vigenteDesde son obligatorios"):
        crear_asignacion({"zona": "Norte", "vigenteDesde": date(2025, 10, 1)})
    
    # Sin zona
    with pytest.raises(ValidationError, match="vendedorId, zona y vigenteDesde son obligatorios"):
        crear_asignacion({"vendedorId": "123", "vigenteDesde": date(2025, 10, 1)})
    
    # Sin vigenteDesde
    with pytest.raises(ValidationError, match="vendedorId, zona y vigenteDesde son obligatorios"):
        crear_asignacion({"vendedorId": "123", "zona": "Norte"})


def test_crear_asignacion_vendedor_no_existe(app_ctx):
    """Test que valida que el vendedor exista"""
    with pytest.raises(NotFoundError, match="vendedor no encontrado"):
        crear_asignacion({
            "vendedorId": "vendedor-inexistente",
            "zona": "Norte",
            "vigenteDesde": date(2025, 10, 1)
        })


def test_cerrar_asignacion_no_existe(app_ctx):
    """Test que valida cerrar asignación inexistente"""
    with pytest.raises(NotFoundError, match="asignación no encontrada"):
        cerrar_asignacion("asignacion-inexistente", date(2025, 10, 7))


def test_listar_asignaciones_con_filtros(app_ctx):
    """Test de listar asignaciones con diferentes filtros"""
    # Crear vendedores
    v1 = crear_vendedor({
        "nombre": "Vendedor1",
        "apellidos": "Test1",
        "correo": "v1@example.com",
        "celular": "3001111111"
    })
    v2 = crear_vendedor({
        "nombre": "Vendedor2",
        "apellidos": "Test2",
        "correo": "v2@example.com",
        "celular": "3002222222"
    })
    
    # Crear asignaciones
    a1 = crear_asignacion({"vendedorId": v1["id"], "zona": "Norte", "vigenteDesde": date(2025, 10, 1)})
    a2 = crear_asignacion({"vendedorId": v1["id"], "zona": "Sur", "vigenteDesde": date(2025, 10, 1)})
    a3 = crear_asignacion({"vendedorId": v2["id"], "zona": "Norte", "vigenteDesde": date(2025, 10, 1)})
    
    # Cerrar una asignación
    cerrar_asignacion(a2["id"], date(2025, 10, 7))
    
    # Filtrar por vendedor
    lista_v1 = listar_asignaciones(vendedor_id=v1["id"])
    assert lista_v1["total"] == 2
    
    # Filtrar por zona
    lista_norte = listar_asignaciones(zona="Norte")
    assert lista_norte["total"] == 2
    
    # Filtrar por activas
    lista_activas = listar_asignaciones(activas=True)
    assert lista_activas["total"] == 2
    
    lista_inactivas = listar_asignaciones(activas=False)
    assert lista_inactivas["total"] == 1
    
    # Filtrar por vendedor y activas
    lista_v1_activas = listar_asignaciones(vendedor_id=v1["id"], activas=True)
    assert lista_v1_activas["total"] == 1


def test_listar_asignaciones_paginacion(app_ctx):
    """Test de paginación en listar_asignaciones"""
    v = crear_vendedor({
        "nombre": "Vendedor",
        "apellidos": "Paginacion",
        "correo": "paginacion@example.com",
        "celular": "3003333333"
    })
    
    # Crear 5 asignaciones
    for i in range(5):
        crear_asignacion({
            "vendedorId": v["id"],
            "zona": f"Zona{i}",
            "vigenteDesde": date(2025, 10, i+1)
        })
    
    # Página 1, 2 items
    lista_p1 = listar_asignaciones(vendedor_id=v["id"], page=1, size=2)
    assert lista_p1["total"] == 5
    assert len(lista_p1["items"]) == 2
    assert lista_p1["page"] == 1
    assert lista_p1["size"] == 2
    
    # Página 2, 2 items
    lista_p2 = listar_asignaciones(vendedor_id=v["id"], page=2, size=2)
    assert len(lista_p2["items"]) == 2
    assert lista_p2["page"] == 2


def test_crear_asignacion_con_vigente_hasta(app_ctx):
    """Test crear asignación con fecha de fin"""
    v = crear_vendedor({
        "nombre": "Test",
        "apellidos": "VigenteHasta",
        "correo": "vigente@example.com",
        "celular": "3004444444"
    })
    
    a = crear_asignacion({
        "vendedorId": v["id"],
        "zona": "Centro",
        "vigenteDesde": date(2025, 10, 1),
        "vigenteHasta": date(2025, 10, 31),
        "activa": False
    })
    
    assert a["vigenteHasta"] == "2025-10-31"
    assert a["activa"] is False
