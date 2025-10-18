# Usa una imagen base de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Instala curl para health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requerimientos
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY . .

# Expone el puerto en el que correrá la aplicación
EXPOSE 5003

# Define el comando para ejecutar la aplicación con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "4", "--timeout", "120", "app:app"]
