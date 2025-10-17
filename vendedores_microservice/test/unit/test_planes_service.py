import pytest
from app.services.vendedores_service import crear_vendedor
from app.services.planes_service import crear_o_actualizar_plan, listar_planes
from app.utils.errors import ValidationError, NotFoundError


def test_crear_y_actualizar_plan(app_ctx):
    """Test crear y actualizar plan de venta"""
    v = crear_vendedor({
        "nombre": "Carlos",
        "apellidos": "Ramírez",
        "correo": "carlos.ramirez@example.com",
        "celular": "3009876543"
    })
    
    # Crear plan
    p = crear_o_actualizar_plan({
        "vendedorId": v["id"],
        "periodo": "2025-10",
        "objetivoMensual": 1000000
    })
    assert p["periodo"] == "2025-10"
    assert p["objetivoMensual"] == 1000000
    assert p["vendedorId"] == v["id"]
    
    # Actualizar mismo periodo
    p2 = crear_o_actualizar_plan({
        "vendedorId": v["id"],
        "periodo": "2025-10",
        "objetivoMensual": 2000000
    })
    assert p2["objetivoMensual"] == 2000000
    assert p2["id"] == p["id"]  # Mismo plan, actualizado
    
    # Verificar que solo hay un plan
    lista = listar_planes(vendedor_id=v["id"])
    assert lista["total"] == 1


def test_plan_validaciones(app_ctx):
    """Test validaciones de crear_o_actualizar_plan"""
    # vendedor no existe
    with pytest.raises(NotFoundError, match="vendedor no encontrado"):
        crear_o_actualizar_plan({
            "vendedorId": "nope",
            "periodo": "2025-10",
            "objetivoMensual": 1
        })
    
    # faltan campos - sin periodo
    with pytest.raises(ValidationError, match="vendedorId, periodo y objetivoMensual son obligatorios"):
        crear_o_actualizar_plan({
            "vendedorId": "x",
            "objetivoMensual": 1000
        })
    
    # faltan campos - sin objetivoMensual
    with pytest.raises(ValidationError, match="vendedorId, periodo y objetivoMensual son obligatorios"):
        crear_o_actualizar_plan({
            "vendedorId": "x",
            "periodo": "2025-10"
        })
    
    # faltan campos - sin vendedorId
    with pytest.raises(ValidationError, match="vendedorId, periodo y objetivoMensual son obligatorios"):
        crear_o_actualizar_plan({
            "periodo": "2025-10",
            "objetivoMensual": 1000
        })


def test_crear_plan_con_meta_unidades(app_ctx):
    """Test crear plan con metaUnidades"""
    v = crear_vendedor({
        "nombre": "Test",
        "apellidos": "MetaUnidades",
        "correo": "meta@example.com",
        "celular": "3001111111"
    })
    
    p = crear_o_actualizar_plan({
        "vendedorId": v["id"],
        "periodo": "2025-11",
        "objetivoMensual": 5000000,
        "metaUnidades": 100
    })
    
    assert p["metaUnidades"] == 100
    assert p["objetivoMensual"] == 5000000


def test_actualizar_plan_con_estado(app_ctx):
    """Test actualizar estado del plan"""
    v = crear_vendedor({
        "nombre": "Test",
        "apellidos": "Estado",
        "correo": "estado@example.com",
        "celular": "3002222222"
    })
    
    # Crear plan activo
    p1 = crear_o_actualizar_plan({
        "vendedorId": v["id"],
        "periodo": "2025-12",
        "objetivoMensual": 3000000,
        "estado": "activo"
    })
    assert p1["estado"] == "activo"
    
    # Actualizar a inactivo
    p2 = crear_o_actualizar_plan({
        "vendedorId": v["id"],
        "periodo": "2025-12",
        "objetivoMensual": 3000000,
        "estado": "inactivo"
    })
    assert p2["estado"] == "inactivo"
    assert p2["id"] == p1["id"]


def test_listar_planes_con_filtros(app_ctx):
    """Test listar planes con filtros"""
    v1 = crear_vendedor({
        "nombre": "Vendedor1",
        "apellidos": "Planes1",
        "correo": "v1planes@example.com",
        "celular": "3003333333"
    })
    v2 = crear_vendedor({
        "nombre": "Vendedor2",
        "apellidos": "Planes2",
        "correo": "v2planes@example.com",
        "celular": "3004444444"
    })
    
    # Crear planes
    crear_o_actualizar_plan({
        "vendedorId": v1["id"],
        "periodo": "2025-10",
        "objetivoMensual": 1000000
    })
    crear_o_actualizar_plan({
        "vendedorId": v1["id"],
        "periodo": "2025-11",
        "objetivoMensual": 1200000
    })
    crear_o_actualizar_plan({
        "vendedorId": v2["id"],
        "periodo": "2025-10",
        "objetivoMensual": 1500000
    })
    
    # Filtrar por vendedor
    lista_v1 = listar_planes(vendedor_id=v1["id"])
    assert lista_v1["total"] == 2
    
    lista_v2 = listar_planes(vendedor_id=v2["id"])
    assert lista_v2["total"] == 1
    
    # Filtrar por periodo
    lista_oct = listar_planes(periodo="2025-10")
    assert lista_oct["total"] == 2
    
    lista_nov = listar_planes(periodo="2025-11")
    assert lista_nov["total"] == 1
    
    # Filtrar por vendedor y periodo
    lista_v1_oct = listar_planes(vendedor_id=v1["id"], periodo="2025-10")
    assert lista_v1_oct["total"] == 1
    assert lista_v1_oct["items"][0]["objetivoMensual"] == 1000000


def test_listar_planes_paginacion(app_ctx):
    """Test paginación en listar_planes"""
    v = crear_vendedor({
        "nombre": "Vendedor",
        "apellidos": "Paginacion",
        "correo": "paginacion.planes@example.com",
        "celular": "3005555555"
    })
    
    # Crear 5 planes para diferentes meses
    for i in range(1, 6):
        crear_o_actualizar_plan({
            "vendedorId": v["id"],
            "periodo": f"2025-{i:02d}",
            "objetivoMensual": i * 1000000
        })
    
    # Página 1, 2 items
    lista_p1 = listar_planes(vendedor_id=v["id"], page=1, size=2)
    assert lista_p1["total"] == 5
    assert len(lista_p1["items"]) == 2
    assert lista_p1["page"] == 1
    assert lista_p1["size"] == 2
    
    # Página 2, 2 items
    lista_p2 = listar_planes(vendedor_id=v["id"], page=2, size=2)
    assert len(lista_p2["items"]) == 2
    assert lista_p2["page"] == 2
    
    # Página 3, 1 item
    lista_p3 = listar_planes(vendedor_id=v["id"], page=3, size=2)
    assert len(lista_p3["items"]) == 1


def test_listar_planes_sin_filtros(app_ctx):
    """Test listar todos los planes sin filtros"""
    v1 = crear_vendedor({
        "nombre": "Test1",
        "apellidos": "SinFiltros",
        "correo": "test1.sf@example.com",
        "celular": "3006666666"
    })
    v2 = crear_vendedor({
        "nombre": "Test2",
        "apellidos": "SinFiltros",
        "correo": "test2.sf@example.com",
        "celular": "3007777777"
    })
    
    crear_o_actualizar_plan({
        "vendedorId": v1["id"],
        "periodo": "2025-01",
        "objetivoMensual": 1000000
    })
    crear_o_actualizar_plan({
        "vendedorId": v2["id"],
        "periodo": "2025-01",
        "objetivoMensual": 2000000
    })
    
    # Sin filtros
    lista_todos = listar_planes()
    assert lista_todos["total"] >= 2
