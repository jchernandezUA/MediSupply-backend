from flask import Blueprint

# Crear el blueprint para health check
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint - retorna 200 OK
    """
    return '', 200
