from app.services.vendedores_service import crear_vendedor
from app.services.planes_service import crear_o_actualizar_plan, listar_planes
from app.utils.errors import ValidationError, NotFoundError

def test_crear_y_actualizar_plan(app_ctx):
    v = crear_vendedor({"identificacion": "CC77", "nombre": "Carlos"})
    p = crear_o_actualizar_plan({"vendedorId": v["id"], "periodo": "2025-10", "objetivoMensual": 1000000})
    assert p["periodo"] == "2025-10"
    # update mismo periodo
    p2 = crear_o_actualizar_plan({"vendedorId": v["id"], "periodo": "2025-10", "objetivoMensual": 2000000})
    assert p2["objetivoMensual"] == 2000000
    lista = listar_planes(vendedor_id=v["id"])
    assert lista["total"] == 1

def test_plan_validaciones(app_ctx):
    # vendedor no existe
    try:
        crear_o_actualizar_plan({"vendedorId": "nope", "periodo": "2025-10", "objetivoMensual": 1})
        assert False, "debería lanzar NotFoundError"
    except NotFoundError:
        pass
    # faltan campos
    try:
        crear_o_actualizar_plan({"vendedorId": "x"})
        assert False, "debería lanzar ValidationError"
    except ValidationError:
        pass
