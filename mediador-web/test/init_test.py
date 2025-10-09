def test_create_app_basic():
    from src import create_app
    app = create_app()
    assert app is not None
    # Opcional: comprobar que los blueprints están registrados
    assert 'health' in app.blueprints
    assert 'proveedor' in app.blueprints
