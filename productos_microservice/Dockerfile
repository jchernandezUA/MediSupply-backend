# Dockerfile para el microservicio de productos
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar curl para health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio para uploads
RUN mkdir -p uploads/certificaciones

# Exponer el puerto 5008
EXPOSE 5008

# Variables de entorno por defecto (se pueden sobrescribir)
ENV PORT=5008
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar la aplicación con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5008", "--workers", "4", "--timeout", "120", "run:app"]
