import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from src.blueprints.auth import auth_bp  # Ajusta el import según estructura

# --- Mocks para User y DB ---

class MockUser:
    def __init__(self, email, password, nombre, apellido, is_active=True, id=1):
        self.email = email
        self.password = password
        self.nombre = nombre
        self.apellido = apellido
        self.is_active = is_active
        self.id = id

    def save(self):
        pass

    def to_dict(self):
        return dict(
            id=self.id,
            email=self.email,
            nombre=self.nombre,
            apellido=self.apellido,
            is_active=self.is_active
        )

    def check_password(self, pwd):
        return self.password == pwd

@pytest.fixture
def client(monkeypatch):
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test'
    app.config['TESTING'] = True
    JWTManager(app)
    app.register_blueprint(auth_bp)
    return app.test_client()

def test_signup_success(client, monkeypatch):
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: None)
    monkeypatch.setattr('src.models.user.User.save', lambda self: None)
    monkeypatch.setattr('src.models.user.User.to_dict', lambda self: dict(id=1, email=self.email, nombre=self.nombre, apellido=self.apellido, is_active=True))

    data = {
        "email": "test@example.com",
        "password": "secreto",
        "nombre": "Juan",
        "apellido": "Perez"
    }
    response = client.post('/signup', json=data)
    assert response.status_code == 201
    assert 'access_token' in response.json

def test_signup_missing_fields(client):
    data = {
        "email": "test@example.com",
        "password": "secreto",
        "nombre": "Juan"
        # Falta 'apellido'
    }
    response = client.post('/signup', json=data)
    assert response.status_code == 400
    assert 'error' in response.json

def test_signup_invalid_email(client, monkeypatch):
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: None)
    data = {
        "email": "invalid-email",
        "password": "secreto",
        "nombre": "Juan",
        "apellido": "Perez"
    }
    response = client.post('/signup', json=data)
    assert response.status_code == 400
    assert 'error' in response.json

def test_signup_short_password(client, monkeypatch):
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: None)
    data = {
        "email": "test@example.com",
        "password": "123",
        "nombre": "Juan",
        "apellido": "Perez"
    }
    response = client.post('/signup', json=data)
    assert response.status_code == 400
    assert 'error' in response.json

def test_signup_user_exists(client, monkeypatch):
    user = MockUser("test@example.com", "secreto", "Juan", "Perez")
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: user)
    data = {
        "email": "test@example.com",
        "password": "secreto",
        "nombre": "Juan",
        "apellido": "Perez"
    }
    response = client.post('/signup', json=data)
    assert response.status_code == 409
    assert 'error' in response.json

def test_login_success(client, monkeypatch):
    user = MockUser("test@example.com", "secreto", "Juan", "Perez")
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: user)
    monkeypatch.setattr('src.models.user.User.check_password', lambda self, pwd: pwd == "secreto")
    monkeypatch.setattr('src.models.user.User.to_dict', lambda self: user.to_dict())
    data = {
        "email": "test@example.com",
        "password": "secreto"
    }
    response = client.post('/login', json=data)
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_login_incorrect_password(client, monkeypatch):
    user = MockUser("test@example.com", "secreto", "Juan", "Perez")
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: user)
    monkeypatch.setattr('src.models.user.User.check_password', lambda self, pwd: False)
    data = {
        "email": "test@example.com",
        "password": "incorrecto"
    }
    response = client.post('/login', json=data)
    assert response.status_code == 401

def test_login_inactive_user(client, monkeypatch):
    user = MockUser("test@example.com", "secreto", "Juan", "Perez", is_active=False)
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: user)
    monkeypatch.setattr('src.models.user.User.check_password', lambda self, pwd: True)
    data = {
        "email": "test@example.com",
        "password": "secreto"
    }
    response = client.post('/login', json=data)
    assert response.status_code == 401
    assert 'error' in response.json

def test_validate_token(client, monkeypatch):
    user = MockUser("test@example.com", "secreto", "Juan", "Perez")
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: user)
    monkeypatch.setattr('src.models.user.User.check_password', lambda self, pwd: True)
    monkeypatch.setattr('src.models.user.User.find_by_id', lambda id: user)
    monkeypatch.setattr('src.models.user.User.to_dict', lambda self: user.to_dict())
    login_data = {"email": "test@example.com", "password": "secreto"}
    response_login = client.post('/login', json=login_data)
    assert 'access_token' in response_login.json
    access_token = response_login.json['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post('/validate', headers=headers)
    assert response.status_code == 200
    assert response.json['valid'] is True

def test_validate_token_user_not_found(client, monkeypatch):
    monkeypatch.setattr('src.models.user.User.find_by_id', lambda id: None)
    login_data = {"email": "test@example.com", "password": "secreto"}
    # Mock login para obtener access_token válido
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: MockUser("test@example.com", "secreto", "Juan", "Perez"))
    monkeypatch.setattr('src.models.user.User.check_password', lambda self, pwd: True)
    response_login = client.post('/login', json=login_data)
    access_token = response_login.json['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post('/validate', headers=headers)
    assert response.status_code == 401
    assert not response.json['valid']
    assert 'error' in response.json

def test_validate_token_inactive_user(client, monkeypatch):
    user = MockUser("test@example.com", "secreto", "Juan", "Perez", is_active=False)
    monkeypatch.setattr('src.models.user.User.find_by_id', lambda id: user)
    login_data = {"email": "test@example.com", "password": "secreto"}
    monkeypatch.setattr('src.models.user.User.find_by_email', lambda email: MockUser("test@example.com", "secreto", "Juan", "Perez"))
    monkeypatch.setattr('src.models.user.User.check_password', lambda self, pwd: True)
    response_login = client.post('/login', json=login_data)
    access_token = response_login.json['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post('/validate', headers=headers)
    assert response.status_code == 401
    assert not response.json['valid']
    assert 'error' in response.json
