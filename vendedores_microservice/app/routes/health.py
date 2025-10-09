from flask import Blueprint, jsonify

bp_health = Blueprint("health", __name__)

@bp_health.get("/health")
def health():
    return jsonify(ok=True, service="vendedores", version="v1"), 200
