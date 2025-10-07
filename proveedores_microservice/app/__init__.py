from flask import Flask
from .extensions import db, ma
from .config import Config
from .routes.proveedores_bp import proveedores_bp
import os

def create_app():
    app = Flask(__name__)
    
    # Usar configuración de testing si está en modo test
    if os.getenv('TESTING') == 'true':
        from .config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    # Debug: mostrar qué BD está usando
    print(f"🗃️  Base de datos configurada: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Crear directorio de uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Inicializar extensiones
    db.init_app(app)
    ma.init_app(app)

    # Registrar blueprints
    app.register_blueprint(proveedores_bp, url_prefix="/api/proveedores")

    # Manejar error 413 (archivo muy grande)
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return {
            "error": "El archivo excede el tamaño máximo permitido de 5MB",
            "codigo": "ARCHIVO_MUY_GRANDE",
            "tamaño_maximo": "5MB"
        }, 413

    # Crear tablas si no existen (solo para pruebas locales)
    with app.app_context():
        db.create_all()

    return app
