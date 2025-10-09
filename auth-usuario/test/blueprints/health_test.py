import pytest
from flask import Flask
from src.blueprints.health import health_bp  # Ajusta ruta si es necesario

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    app.config['TESTING'] = True
    return app.test_client()

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.data == b''  # El cuerpo está vacío
