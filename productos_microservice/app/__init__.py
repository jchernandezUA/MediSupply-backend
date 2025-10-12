from flask import Flask
from .extensions import db, ma
from .config import Config
from .routes.productos_bp import productos_bp
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
    app.register_blueprint(productos_bp)

    # Crear tablas si no existen
    with app.app_context():
        db.create_all()

    return app
