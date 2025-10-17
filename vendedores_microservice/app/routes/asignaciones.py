from flask import Blueprint, jsonify, request
from datetime import date
from app.services.asignaciones_service import crear_asignacion, cerrar_asignacion, listar_asignaciones

bp_asignaciones = Blueprint("asignaciones", __name__)

@bp_asignaciones.post("/vendedores/<string:v_id>/asignaciones")
def post_asignacion(v_id: str):
    payload = request.get_json(force=True, silent=True) or {}
    payload["vendedorId"] = v_id
    # Convertir fecha string a objeto date si viene como string
    if "vigenteDesde" in payload and isinstance(payload["vigenteDesde"], str):
        payload["vigenteDesde"] = date.fromisoformat(payload["vigenteDesde"])
    if "vigenteHasta" in payload and isinstance(payload["vigenteHasta"], str):
        payload["vigenteHasta"] = date.fromisoformat(payload["vigenteHasta"])
    data = crear_asignacion(payload)
    return jsonify(data), 201

@bp_asignaciones.post("/asignaciones")
def post_asignacion_directo():
    """Ruta alternativa para crear asignación con vendedorId en el body"""
    payload = request.get_json(force=True, silent=True) or {}
    # Convertir fecha string a objeto date si viene como string
    if "vigenteDesde" in payload and isinstance(payload["vigenteDesde"], str):
        payload["vigenteDesde"] = date.fromisoformat(payload["vigenteDesde"])
    if "vigenteHasta" in payload and isinstance(payload["vigenteHasta"], str):
        payload["vigenteHasta"] = date.fromisoformat(payload["vigenteHasta"])
    data = crear_asignacion(payload)
    return jsonify(data), 201

@bp_asignaciones.patch("/asignaciones/<string:asign_id>/cerrar")
def patch_cerrar_asignacion(asign_id: str):
    body = request.get_json(force=True, silent=True) or {}
    hasta = body.get("vigenteHasta")
    # admite ISO YYYY-MM-DD, si falta usa hoy
    hasta_fecha = date.fromisoformat(hasta) if hasta else date.today()
    data = cerrar_asignacion(asign_id, hasta_fecha)
    return jsonify(data), 200

@bp_asignaciones.patch("/asignaciones/<string:asign_id>")
def patch_asignacion(asign_id: str):
    """Ruta alternativa para cerrar asignación"""
    body = request.get_json(force=True, silent=True) or {}
    hasta = body.get("vigenteHasta")
    # admite ISO YYYY-MM-DD, si falta usa hoy
    hasta_fecha = date.fromisoformat(hasta) if hasta else date.today()
    data = cerrar_asignacion(asign_id, hasta_fecha)
    return jsonify(data), 200

@bp_asignaciones.get("/asignaciones")
def get_asignaciones():
    vendedor_id = request.args.get("vendedorId")
    zona = request.args.get("zona")
    activas = request.args.get("activas")
    activas_bool = None if activas is None else activas.lower() in ("true", "1", "yes")
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))
    data = listar_asignaciones(
        vendedor_id=vendedor_id, zona=zona, activas=activas_bool, page=page, size=size
    )
    return jsonify(data), 200
