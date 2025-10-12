# Dockerfile para el microservicio de productos
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio para uploads
RUN mkdir -p uploads/certificaciones

# Exponer el puerto 5001
EXPOSE 5001

# Variables de entorno por defecto (se pueden sobrescribir)
ENV PORT=5001
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar la aplicación
CMD ["python", "run.py"]
