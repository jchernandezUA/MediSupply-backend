from flask import Flask
from flask_jwt_extended import JWTManager
from src.config.config import Config
from src.blueprints.health import health_bp
from src.blueprints.auth import auth_bp
from src.blueprints.productos import producto_bp

def create_app(config_class=Config):
    """
    Factory function para crear la aplicación Flask
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar JWT
    jwt = JWTManager(app)
    
    # Registrar blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(producto_bp)
    
    return app
