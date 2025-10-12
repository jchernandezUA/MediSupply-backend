import pytest
import tempfile
import os
from app import create_app
from app.extensions import db

@pytest.fixture
def app():
    """Crear aplicación de prueba"""
    app = create_app()
    # Usar la configuración específica de testing
    app.config.from_object('app.config.TestingConfig')
    # Override del directorio de uploads para tests
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Cliente de prueba para hacer requests"""
    return app.test_client()
