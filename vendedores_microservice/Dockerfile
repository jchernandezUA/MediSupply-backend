# Imagen base
FROM python:3.11-slim

# Evitar bytecode y forzar stdout sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Crear directorio de la app
WORKDIR /app

# Instalar dependencias del sistema (psycopg, build, curl para healthcheck opcional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copiar requisitos primero para aprovechar cache
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && pip install gunicorn

# Copiar el resto del código
COPY . /app

# Puerto del servicio
EXPOSE 8001

# Variables por defecto (se pueden sobrescribir en compose)
ENV FLASK_APP=app:create_app \
    SERVICE_PORT=8001

CMD ["python", "run.py"]
