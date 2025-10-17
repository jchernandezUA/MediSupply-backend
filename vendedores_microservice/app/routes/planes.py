from flask import Blueprint, jsonify, request
from app.services.planes_service import crear_o_actualizar_plan, listar_planes

bp_planes = Blueprint("planes", __name__)

@bp_planes.post("/planes-venta")
def post_plan():
    payload = request.get_json(force=True, silent=True) or {}
    data = crear_o_actualizar_plan(payload)
    return jsonify(data), 201

@bp_planes.post("/planes")
def post_plan_alternativo():
    """Ruta alternativa para crear/actualizar plan"""
    payload = request.get_json(force=True, silent=True) or {}
    data = crear_o_actualizar_plan(payload)
    return jsonify(data), 201

@bp_planes.get("/planes-venta")
def get_planes():
    vendedor_id = request.args.get("vendedorId")
    periodo = request.args.get("periodo")
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))
    data = listar_planes(vendedor_id=vendedor_id, periodo=periodo, page=page, size=size)
    return jsonify(data), 200

@bp_planes.get("/planes")
def get_planes_alternativo():
    """Ruta alternativa para listar planes"""
    vendedor_id = request.args.get("vendedorId")
    periodo = request.args.get("periodo")
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))
    data = listar_planes(vendedor_id=vendedor_id, periodo=periodo, page=page, size=size)
    return jsonify(data), 200
