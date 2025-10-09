from datetime import date
from app.services.vendedores_service import crear_vendedor
from app.services.asignaciones_service import crear_asignacion, cerrar_asignacion, listar_asignaciones

def test_asignar_y_cerrar(app_ctx):
    v = crear_vendedor({"identificacion": "CC88", "nombre": "Luisa"})
    a = crear_asignacion({"vendedorId": v["id"], "zona": "Occidente", "vigenteDesde": date(2025, 10, 1)})
    assert a["activa"] is True
    cerrada = cerrar_asignacion(a["id"], date(2025, 10, 7))
    assert cerrada["activa"] is False
    lista = listar_asignaciones(vendedor_id=v["id"], activas=False)
    assert lista["total"] == 1 and lista["items"][0]["zona"] == "Occidente"
