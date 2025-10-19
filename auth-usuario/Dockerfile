# Imagen base de Python
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias (incluyendo gunicorn explícitamente)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 5001

# Variables de entorno
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=5001

# Comando para ejecutar la aplicación
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
