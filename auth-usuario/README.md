# Auth Usuario Microservice

Microservicio de autenticación desarrollado con Python y Flask que maneja login, signup y JWT con PostgreSQL.

## Características

- ✅ Health check endpoint (200 OK)
- ✅ Registro de usuarios (signup)
- ✅ Login con JWT (sin expiración)
- ✅ Validación de token
- ✅ Perfil de usuario
- ✅ Base de datos PostgreSQL
- ✅ Encriptación de contraseñas con bcrypt
- ✅ Configuración para Docker
- ✅ Producción lista con Gunicorn
- ✅ Usuario no-root para seguridad

## Arquitectura

```
auth-usuario/
├── src/
│   ├── __init__.py          # Factory function de la aplicación
│   ├── config/              # Configuración con PostgreSQL
│   │   ├── __init__.py
│   │   └── config.py
│   ├── models/              # Modelos de datos
│   │   ├── __init__.py
│   │   └── user.py          # Modelo de usuario
│   └── blueprints/          # Blueprints del microservicio
│       ├── __init__.py
│       ├── health.py        # Health check endpoint
│       └── auth.py          # Endpoints de autenticación
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
Retorna 200 OK - endpoint de salud del microservicio.

### Registro de Usuario
```
POST /auth/signup
```
Registra un nuevo usuario y retorna JWT tokens.

**Ejemplo de request:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123",
  "nombre": "Juan",
  "apellido": "Pérez"
}
```

**Ejemplo de response (201):**
```json
{
  "message": "Usuario creado exitosamente",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "nombre": "Juan",
    "apellido": "Pérez",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Login
```
POST /auth/login
```
Inicia sesión y retorna JWT tokens.

**Ejemplo de request:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123"
}
```

**Ejemplo de response (200):**
```json
{
  "message": "Login exitoso",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "nombre": "Juan",
    "apellido": "Pérez",
    "is_active": true
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Validar Token
```
POST /auth/validate
```
Valida si el token JWT es válido y el usuario está activo.

**Headers requeridos:**
```
Authorization: Bearer <access_token>
```

**Ejemplo de response (200) - Token válido:**
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "nombre": "Juan",
    "apellido": "Pérez",
    "is_active": true
  },
  "message": "Token válido"
}
```

**Ejemplo de response (401) - Token inválido:**
```json
{
  "valid": false,
  "error": "Usuario no encontrado"
}
```

### Perfil de Usuario
```
GET /auth/profile
```
Obtiene el perfil del usuario autenticado.

**Headers requeridos:**
```
Authorization: Bearer <access_token>
```

## Desarrollo Local

### Prerrequisitos
- Python 3.11+
- PostgreSQL
- pip

### Instalación

1. Clonar el repositorio
2. Navegar al directorio del microservicio:
   ```bash
   cd auth-usuario
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

5. Configurar base de datos PostgreSQL:
   - Crear base de datos: `medsupply`
   - Configurar variables de entorno (ver sección Variables de Entorno)

6. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

La aplicación estará disponible en `http://localhost:5001`

### Probar los Endpoints
```bash
# Health check
curl http://localhost:5001/health

# Registro de usuario
curl -X POST http://localhost:5001/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@ejemplo.com",
    "password": "password123",
    "nombre": "Juan",
    "apellido": "Pérez"
  }'

# Login
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@ejemplo.com",
    "password": "password123"
  }'

# Validar token
curl -X POST http://localhost:5001/auth/validate \
  -H "Authorization: Bearer <access_token>"
```

## Docker

### Construir la imagen
```bash
docker build -t auth-usuario .
```

### Ejecutar el contenedor
```bash
docker run -p 5001:5001 \
  -e DB_HOST=localhost \
  -e DB_NAME=medsupply \
  -e DB_USER=postgres \
  -e DB_PASSWORD=password \
  auth-usuario
```

### Ejecutar con Docker Compose (recomendado)
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: medsupply
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  auth-usuario:
    build: .
    ports:
      - "5001:5001"
    environment:
      DB_HOST: postgres
      DB_NAME: medsupply
      DB_USER: postgres
      DB_PASSWORD: password
    depends_on:
      - postgres

volumes:
  postgres_data:
```

## Variables de Entorno

- `HOST`: Host del servidor (default: 0.0.0.0)
- `PORT`: Puerto en el que se ejecutará la aplicación (default: 5001)
- `DEBUG`: Modo debug (default: false)
- `SECRET_KEY`: Clave secreta para Flask
- `JWT_SECRET_KEY`: Clave secreta para JWT
- `DB_HOST`: Host de PostgreSQL (default: localhost)
- `DB_PORT`: Puerto de PostgreSQL (default: 5432)
- `DB_NAME`: Nombre de la base de datos (default: medsupply)
- `DB_USER`: Usuario de PostgreSQL (default: postgres)
- `DB_PASSWORD`: Contraseña de PostgreSQL (default: password)

## Tecnologías Utilizadas

- **Flask**: Framework web de Python
- **Flask-SQLAlchemy**: ORM para base de datos
- **Flask-JWT-Extended**: Manejo de JWT tokens
- **PostgreSQL**: Base de datos
- **bcrypt**: Encriptación de contraseñas
- **Gunicorn**: Servidor WSGI para producción
- **Docker**: Containerización
- **Python 3.11**: Lenguaje de programación

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request
