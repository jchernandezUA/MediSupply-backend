import os
from flask import Flask
from .models import db
from .routes.errors import register_error_handlers
from .routes.health import bp_health
from .routes.vendedores import bp_vendedores
from .routes.planes import bp_planes
from .routes.asignaciones import bp_asignaciones

def create_app():
    app = Flask(__name__)
    app.config["APP_NAME"] = "vendedores_microservice"
    
    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL', 'postgresql+psycopg2://user:pass@localhost:5432/vendedores')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar SQLAlchemy
    db.init_app(app)
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()

    # Blueprints
    app.register_blueprint(bp_health, url_prefix="/v1")
    app.register_blueprint(bp_vendedores, url_prefix="/v1")
    app.register_blueprint(bp_planes, url_prefix="/v1")
    app.register_blueprint(bp_asignaciones, url_prefix="/v1")

    # Errores → HTTP
    register_error_handlers(app)
    return app
