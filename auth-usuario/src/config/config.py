import os

class Config:
    """
    Configuración del microservicio auth-usuario
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5003))
    
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'medsupply')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = False
    
    BCRYPT_LOG_ROUNDS = 12


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    # Usar base de datos en memoria para pruebas
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Puede configurarse para no tener token que expire y otras variables específicas para testing
    JWT_ACCESS_TOKEN_EXPIRES = False
