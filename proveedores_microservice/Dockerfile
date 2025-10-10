# Imagen base de Python
FROM python:3.10-slim

# Directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorio para uploads
RUN mkdir -p uploads/certificaciones

# Exponer puerto
EXPOSE 5000

# Variable de entorno para Python
ENV PYTHONUNBUFFERED=1
# Variables de entorno
ENV PORT=5000

# Comando para ejecutar la aplicación
CMD ["python", "run.py"]
