import pytest
from src import create_app
from src.models.user import User, db

class DummyQuery:
    def __init__(self, user=None):
        self._user = user

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self._user

    def get(self, id):
        if self._user and self._user.id == id:
            return self._user
        return None

class DummySession:
    def __call__(self):
        return self

    def __init__(self):
        self.committed = False
        self.added = []
        self.deleted = []

    def add(self, instance):
        self.added.append(instance)

    def commit(self):
        self.committed = True

    def delete(self, instance):
        self.deleted.append(instance)

@pytest.fixture(scope='module')
def app():
    app = create_app(testing=True)
    with app.app_context():
        yield app

@pytest.fixture
def dummy_user():
    return User(
        email="test@example.com",
        password="mypassword",
        nombre="Test",
        apellido="User"
    )

@pytest.fixture
def dummy_db_session(monkeypatch):
    session = DummySession()
    # Mock db.session para evitar acceso real a base de datos
    monkeypatch.setattr(db, 'session', session)
    # Mock User.query para las pruebas que requieren consulta
    monkeypatch.setattr(User, 'query', DummyQuery())
    return session

def test_password_hashing(dummy_user):
    assert dummy_user.password_hash != "mypassword"
    assert dummy_user.check_password("mypassword") is True
    assert dummy_user.check_password("wrongpass") is False

def test_to_dict_returns_expected_keys(dummy_user):
    d = dummy_user.to_dict()
    keys = ['id', 'email', 'nombre', 'apellido', 'is_active', 'created_at', 'updated_at']
    for key in keys:
        assert key in d
    assert d['email'] == dummy_user.email

def test_find_by_email(monkeypatch, dummy_user, app):
    with app.app_context():
        dummy_query = DummyQuery(user=dummy_user)
        monkeypatch.setattr(User, 'query', dummy_query)
        found = User.find_by_email("test@example.com")
        assert found == dummy_user
        found_lower = User.find_by_email("TEST@EXAMPLE.COM")
        assert found_lower == dummy_user

def test_find_by_id(monkeypatch, dummy_user, app):
    with app.app_context():
        dummy_query = DummyQuery(user=dummy_user)
        monkeypatch.setattr(User, 'query', dummy_query)
        found = User.find_by_id(dummy_user.id)
        assert found == dummy_user
        not_found = User.find_by_id(999)
        assert not_found is None

def test_save_and_delete(dummy_user, dummy_db_session):
    dummy_user.save()
    assert dummy_user in dummy_db_session.added
    assert dummy_db_session.committed is True

    dummy_db_session.committed = False  # Reset commit flag
    dummy_user.delete()
    assert dummy_user in dummy_db_session.deleted
    assert dummy_db_session.committed is True

def test_repr_returns_email(dummy_user):
    rep = repr(dummy_user)
    assert dummy_user.email in rep
