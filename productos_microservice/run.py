import os

# Cargar variables de entorno ANTES de importar la app
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()
    print(f"🔧 Variables cargadas - DATABASE_URL: {os.getenv('DATABASE_URL', 'No encontrada')}")

from app import create_app

# Crear la app a nivel de módulo para que Gunicorn pueda encontrarla
app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=os.getenv("PORT", 5008))  # Puerto 5008 para productos
