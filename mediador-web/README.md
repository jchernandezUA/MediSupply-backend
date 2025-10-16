# Mediador Web BFF

Backend for Frontend (BFF) desarrollado con Python y Flask que actúa como mediador entre el frontend y los microservicios.

## Características

- ✅ Health check endpoint (200 OK)
- ✅ BFF para microservicio de proveedores
- ✅ POST /proveedor que se conecta al micro de proveedores
- ✅ Validación JWT requerida para crear proveedores
- ✅ Configuración para Docker
- ✅ Producción lista con Gunicorn
- ✅ Usuario no-root para seguridad

## Arquitectura

```
mediador-web/
├── src/
│   ├── __init__.py          # Factory function de la aplicación
│   ├── config/              # Configuración simple
│   │   ├── __init__.py
│   │   └── config.py
│   └── blueprints/          # Blueprints del BFF
│       ├── __init__.py
│       ├── health.py        # Health check endpoint
│       └── proveedor.py     # BFF para proveedores
├── app.py                   # Punto de entrada principal
├── requirements.txt
├── Dockerfile
└── README.md
```

## Endpoints

### Health Check
```
GET /health
```
Retorna 200 OK - endpoint de salud del BFF.

### Crear Proveedor (BFF)
```
POST /proveedor
```
BFF que se conecta al microservicio de proveedores. **Requiere autenticación JWT válida**. Si el microservicio responde con 201, retorna 201 con los datos del proveedor creado.

**Headers requeridos:**
```
Authorization: Bearer <access_token>
```

**Ejemplo de request:**
```json
{
  "nombre": "Proveedor ABC",
  "email": "contacto@proveedor.com",
  "telefono": "+1234567890"
}
```

**Ejemplo de response (201):**
```json
{
  "id": 1,
  "nombre": "Proveedor ABC",
  "email": "contacto@proveedor.com",
  "telefono": "+1234567890",
  "fecha_creacion": "2024-01-15T10:30:00Z",
  "created_by_user_id": "1"
}
```

## Desarrollo Local

### Prerrequisitos
- Python 3.11+
- pip

### Instalación

1. Clonar el repositorio
2. Navegar al directorio del microservicio:
   ```bash
   cd mediador-web
   ```

3. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

4. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

5. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

La aplicación estará disponible en `http://localhost:5002`

### Probar los Endpoints
```bash
# Health check
curl http://localhost:5002/health

# Crear proveedor (BFF) - Requiere JWT
curl -X POST http://localhost:5002/proveedor \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "nombre": "Proveedor ABC",
    "email": "contacto@proveedor.com",
    "telefono": "+1234567890"
  }'
```

## Docker

### Construir la imagen
```bash
docker build -t mediador-web .
```

### Ejecutar el contenedor
```bash
docker run -p 5002:5002 mediador-web
```

### Ejecutar con variables de entorno
```bash
docker run -p 5002:5002 \
  -e DEBUG=true \
  -e PORT=5002 \
  -e PROVEEDORES_URL=http://localhost:5006 \
  -e JWT_SECRET_KEY=your-jwt-secret-key-here \
  mediador-web
```

## Variables de Entorno

- `HOST`: Host del servidor (default: 0.0.0.0)
- `PORT`: Puerto en el que se ejecutará la aplicación (default: 5002)
- `DEBUG`: Modo debug (default: false)
- `SECRET_KEY`: Clave secreta para Flask (default: dev-secret-key)
- `PROVEEDORES_URL`: URL del microservicio de proveedores (default: http://localhost:5006)
- `AUTH_URL`: URL del microservicio de autenticación (default: http://localhost:5001)
- `JWT_SECRET_KEY`: Clave secreta para validar JWT (debe coincidir con auth-usuario)

## Estructura del Proyecto

```
mediador-web/
├── src/                    # Paquete principal de la aplicación
│   ├── __init__.py        # Factory function de la aplicación
│   ├── config/            # Configuración simple
│   │   ├── __init__.py
│   │   └── config.py
│   └── blueprints/        # Blueprints del BFF
│       ├── __init__.py
│       ├── health.py      # Health check endpoint
│       └── proveedor.py   # BFF para proveedores
├── app.py                 # Punto de entrada principal
├── requirements.txt       # Dependencias de Python
├── Dockerfile            # Configuración de Docker
├── .dockerignore         # Archivos a ignorar en Docker
└── README.md             # Este archivo
```

## Tecnologías Utilizadas

- **Flask**: Framework web de Python
- **Requests**: Librería para hacer llamadas HTTP a otros microservicios
- **Gunicorn**: Servidor WSGI para producción
- **Docker**: Containerización
- **Python 3.11**: Lenguaje de programación

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request
