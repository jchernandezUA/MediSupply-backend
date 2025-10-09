import pytest
from flask import Flask
from unittest.mock import patch
from src.models.user import db, User  # Ajusta según tu estructura real

@pytest.fixture(scope='module')
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # BD en memoria para tests
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

def test_find_by_email_mock(app):
    with app.app_context():
        mock_user = User(
            email="test@example.com",
            password="password123",
            nombre="Test",
            apellido="User"
        )
        with patch('src.models.user.User.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = mock_user
            user = User.find_by_email("test@example.com")
            assert user is not None
            assert user.email == "test@example.com"

def test_save_user_mock(app, mocker):
    with app.app_context():
        user = User("test@example.com", "password123", "Test", "User")
        mock_session = mocker.patch('src.models.user.db.session')
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        saved_user = user.save()
        mock_session.add.assert_called_once_with(user)
        mock_session.commit.assert_called_once()
        assert saved_user == user

def test_check_password_correct(app):
    with app.app_context():
        password = "mypassword"
        user = User("test@example.com", password, "Test", "User")
        assert user.check_password(password) is True

def test_check_password_wrong(app):
    with app.app_context():
        user = User("test@example.com", "mypassword", "Test", "User")
        assert user.check_password("wrongpassword") is False

def test_to_dict_contains_keys(app):
    with app.app_context():
        user = User("test@example.com", "password123", "Nombre", "Apellido")
        user.id = 1
        user.is_active = True
        user.created_at = user.updated_at = None
        user_dict = user.to_dict()
        expected_keys = ['id', 'email', 'nombre', 'apellido', 'is_active', 'created_at', 'updated_at']
        for key in expected_keys:
            assert key in user_dict

def test_find_by_id_mock(app):
    with app.app_context():
        mock_user = User("id@example.com", "pass", "N", "A")
        with patch('src.models.user.User.query') as mock_query:
            mock_query.get.return_value = mock_user
            user = User.find_by_id(5)
            assert user == mock_user
            mock_query.get.assert_called_once_with(5)

def test_delete_mock(app, mocker):
    with app.app_context():
        user = User("delete@example.com", "pass", "N", "A")
        mock_session = mocker.patch('src.models.user.db.session')
        mock_session.delete.return_value = None
        mock_session.commit.return_value = None
        user.delete()
        mock_session.delete.assert_called_once_with(user)
        mock_session.commit.assert_called_once()

def test_repr(app):
    with app.app_context():
        user = User("repr@example.com", "pass", "N", "A")
        repr_str = repr(user)
        assert "repr@example.com" in repr_str
