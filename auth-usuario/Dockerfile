# Usar una imagen base de Python oficial
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY app.py .
COPY src/ ./src/

# Crear un usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Exponer el puerto
EXPOSE 5003

# Variables de entorno
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=5003

# Comando para ejecutar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "2", "--timeout", "120", "app:app"]
