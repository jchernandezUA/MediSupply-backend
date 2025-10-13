from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.config.config import Config
from src.blueprints.health import health_bp
from src.blueprints.proveedores import proveedor_bp
from src.blueprints.auth import auth_bp
from src.blueprints.vendedores import vendedores_bp

def create_app(config_class=Config):
    """
    Factory function para crear la aplicación Flask
    """
    app = Flask(__name__)
    CORS(
        app,
        origins=["https://d2rz3b4ejfic21.cloudfront.net"],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    app.config.from_object(config_class)

    # Inicializar JWT
    jwt = JWTManager(app)
    
    # Registrar blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(proveedor_bp)
    app.register_blueprint(vendedores_bp)

    return app
