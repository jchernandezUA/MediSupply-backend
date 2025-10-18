"""
Tests para el endpoint de health
"""


def test_health_check(client):
    """Test que el endpoint de health funciona"""
    response = client.get('/v1/health')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["service"] == "vendedores"
