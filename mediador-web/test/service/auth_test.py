import pytest
from unittest.mock import patch, MagicMock
from src.services.auth import register_user, login_user, AuthServiceError

valid_register_data = {
    'email': 'user@example.com',
    'password': 'password123',
    'nombre': 'User',
    'apellido': 'Test'
}

valid_login_data = {
    'email': 'user@example.com',
    'password': 'password123'
}

@patch('src.services.auth.requests.post')
def test_register_user_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'id': 1, 'email': valid_register_data['email']}
    mock_post.return_value = mock_response

    result = register_user(valid_register_data)
    assert result['email'] == valid_register_data['email']
    mock_post.assert_called_once_with('http://localhost:5003/auth/signup', json=valid_register_data)

def test_register_user_none_data():
    with pytest.raises(AuthServiceError) as excinfo:
        register_user(None)
    assert excinfo.value.status_code == 400

def test_register_user_missing_fields():
    data = valid_register_data.copy()
    del data['email']
    with pytest.raises(AuthServiceError) as excinfo:
        register_user(data)
    assert 'email' in str(excinfo.value.message).lower()

def test_register_user_invalid_email():
    data = valid_register_data.copy()
    data['email'] = 'invalidemail'
    with pytest.raises(AuthServiceError) as excinfo:
        register_user(data)
    assert 'email inválido' in str(excinfo.value.message).lower()

def test_register_user_short_password():
    data = valid_register_data.copy()
    data['password'] = '123'
    with pytest.raises(AuthServiceError) as excinfo:
        register_user(data)
    assert 'contraseña' in str(excinfo.value.message).lower()

@patch('src.services.auth.requests.post')
def test_register_user_http_error(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 409
    mock_post.return_value = mock_response

    with pytest.raises(AuthServiceError) as excinfo:
        register_user(valid_register_data)
    assert excinfo.value.status_code == 409

@patch('src.services.auth.requests.post')
def test_login_user_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'access_token': 'token123'}
    mock_post.return_value = mock_response

    result = login_user(valid_login_data)
    assert 'access_token' in result
    mock_post.assert_called_once_with('http://localhost:5003/auth/login', json=valid_login_data)

def test_login_user_missing_email_or_password():
    with pytest.raises(AuthServiceError) as excinfo:
        login_user({'email': '', 'password': ''})
    assert excinfo.value.status_code == 400

def test_login_user_invalid_email():
    with pytest.raises(AuthServiceError) as excinfo:
        login_user({'email': 'bademail', 'password': 'password123'})
    assert 'email inválido' in str(excinfo.value.message).lower()

def test_login_user_short_password():
    with pytest.raises(AuthServiceError) as excinfo:
        login_user({'email': 'test@example.com', 'password': '123'})
    assert 'contraseña' in str(excinfo.value.message).lower()
