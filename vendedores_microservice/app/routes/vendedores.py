from flask import Blueprint, jsonify, request
from app.services.vendedores_service import (
    crear_vendedor,
    obtener_vendedor,
    actualizar_vendedor,
    listar_vendedores,
)

bp_vendedores = Blueprint("vendedores", __name__)

@bp_vendedores.post("/vendedores")
def post_vendedor():
    payload = request.get_json(force=True, silent=True) or {}
    data = crear_vendedor(payload)
    return jsonify(data), 201

@bp_vendedores.get("/vendedores/<string:v_id>")
def get_vendedor(v_id: str):
    data = obtener_vendedor(v_id)
    return jsonify(data), 200

@bp_vendedores.patch("/vendedores/<string:v_id>")
def patch_vendedor(v_id: str):
    payload = request.get_json(force=True, silent=True) or {}
    data = actualizar_vendedor(v_id, payload)
    return jsonify(data), 200

@bp_vendedores.get("/vendedores")
def get_vendedores():
    zona = request.args.get("zona")
    estado = request.args.get("estado")
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))
    data = listar_vendedores(zona=zona, estado=estado, page=page, size=size)
    return jsonify(data), 200

