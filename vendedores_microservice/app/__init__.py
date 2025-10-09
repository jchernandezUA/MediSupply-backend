from flask import Flask
from .routes.errors import register_error_handlers
from .routes.health import bp_health
from .routes.vendedores import bp_vendedores
from .routes.planes import bp_planes
from .routes.asignaciones import bp_asignaciones

def create_app():
    app = Flask(__name__)
    app.config["APP_NAME"] = "vendedores_microservice"

    # Blueprints
    app.register_blueprint(bp_health, url_prefix="/v1")
    app.register_blueprint(bp_vendedores, url_prefix="/v1")
    app.register_blueprint(bp_planes, url_prefix="/v1")
    app.register_blueprint(bp_asignaciones, url_prefix="/v1")

    # Errores → HTTP
    register_error_handlers(app)
    return app
