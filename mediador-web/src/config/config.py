import os

class Config:
    """
    Configuración del BFF mediador-web
    """
    # Configuración de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Configuración del servidor
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5002))
    
    # Configuración de microservicios
    PROVEEDORES_URL = os.environ.get('PROVEEDORES_URL', 'http://localhost:5006')
    AUTH_URL = os.environ.get('AUTH_URL', 'http://localhost:5001')
    
    # Configuración de JWT (debe coincidir con auth-usuario)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
