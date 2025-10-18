"""
Configuración de fixtures de pytest para los tests del microservicio de vendedores.
"""
import pytest
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para que pytest pueda encontrar el módulo 'app'
# Obtener el directorio raíz del proyecto (dos niveles arriba desde test/)
root_dir = Path(__file__).parent.parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app import create_app
from app.models import db


@pytest.fixture(scope="session")
def app():
    """Crea una instancia de la aplicación Flask para testing."""
    # Configurar base de datos de prueba en memoria
    os.environ['DB_URL'] = 'sqlite:///:memory:'
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app


@pytest.fixture(scope="function")
def app_ctx(app):
    """
    Crea un contexto de aplicación y una sesión de base de datos limpia para cada test.
    """
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        yield app
        
        # Limpiar después del test
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app_ctx):
    """
    Crea un cliente de prueba para hacer peticiones HTTP.
    Usa app_ctx para asegurar que las tablas estén creadas.
    """
    return app_ctx.test_client()
