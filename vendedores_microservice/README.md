# 🏢 Microservicio de Vendedores - MediSupply

Servicio backend para la gestión de vendedores del sistema MediSupply.

## 📋 Descripción

Microservicio RESTful que implementa la funcionalidad completa para gestionar el equipo comercial de vendedores, incluyendo:
- ✅ Registro de vendedores con validaciones robustas
- ✅ Gestión de planes de venta
- ✅ Asignación de zonas geográficas
- ✅ Auditoría completa de cambios

## 🎯 Historia de Usuario Implementada

**KAN-83: Registrar Vendedor**
- Como Gerente Comercial quiero registrar un nuevo vendedor con nombre, apellidos, correo y celular para poder agregar a los nuevos miembros del equipo comercial.
- Ver detalles completos en: [`CHANGELOG_HU_KAN-83.md`](CHANGELOG_HU_KAN-83.md)

## 🚀 Características

### ✅ Validaciones Implementadas
- Correo electrónico con formato válido
- Celular con mínimo 10 dígitos
- Prevención de duplicados (correo único)
- Campos obligatorios: nombre, apellidos, correo, celular
- Campos opcionales: teléfono, zona

### ✅ Auditoría Completa
- Usuario de creación
- Fecha de creación
- Usuario de última actualización
- Fecha de última actualización

### ✅ Rendimiento
- Índices en campos de búsqueda frecuente
- Paginación en listados
- Filtros por zona y estado

## 🛠️ Tecnologías

- **Python**: 3.10+
- **Flask**: Framework web
- **SQLAlchemy**: ORM
- **PostgreSQL/SQLite**: Base de datos
- **pytest**: Testing

## 📦 Instalación

### 1. Clonar el repositorio
```bash
cd vendedores_microservice
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/medisupply"
export PORT=5002
```

### 5. Inicializar base de datos
```python
from app.models import db
db.create_all()
```

## 🏃 Ejecución

### Modo Desarrollo
```bash
python run.py
```

### Modo Producción
```bash
gunicorn -w 4 -b 0.0.0.0:5002 run:app
```

### Con Docker
```bash
docker-compose up
```

## 🧪 Testing

### Ejecutar todos los tests
```bash
pytest test/unit/ -v
```

### Con cobertura
```bash
pytest --cov=app --cov-report=html
```

### Pruebas manuales
```bash
python test_api_manual.py
```

## 📚 Documentación API

### Endpoints Principales

#### ✅ Crear Vendedor
```bash
POST /vendedores
Content-Type: application/json

{
  "nombre": "Juan Carlos",
  "apellidos": "Pérez García",
  "correo": "juan.perez@medisupply.com",
  "celular": "3001234567",
  "telefono": "6015551234",
  "zona": "Bogotá - Colombia"
}
```

#### ✅ Obtener Vendedor
```bash
GET /vendedores/{id}
```

#### ✅ Actualizar Vendedor
```bash
PATCH /vendedores/{id}
Content-Type: application/json

{
  "zona": "Cali - Colombia",
  "telefono": "6027778888"
}
```

#### ✅ Listar Vendedores
```bash
GET /vendedores?page=1&size=10&zona=Bogotá&estado=activo
```

Ver documentación completa en:
- [`GUIA_INTEGRACION_FRONTEND.md`](GUIA_INTEGRACION_FRONTEND.md) - Para desarrolladores frontend
- [`RESUMEN_EJECUTIVO.md`](RESUMEN_EJECUTIVO.md) - Resumen de implementación

## 📂 Estructura del Proyecto

```
vendedores_microservice/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── vendedor.py           # Modelo principal
│   │   ├── plan_venta.py
│   │   └── asignacion.py
│   ├── routes/
│   │   ├── vendedores.py         # Rutas REST
│   │   ├── planes.py
│   │   ├── asignaciones.py
│   │   └── health.py
│   ├── services/
│   │   ├── vendedores_service.py # Lógica de negocio
│   │   ├── planes_service.py
│   │   └── asignaciones_service.py
│   └── utils/
│       ├── validators.py         # Validadores
│       └── errors.py
├── test/
│   └── unit/
│       ├── test_vendedores_service.py
│       ├── test_validators.py
│       ├── test_planes_service.py
│       └── test_asignaciones_service.py
├── migrations/
│   └── 001_actualizar_modelo_vendedor.sql
├── run.py                        # Punto de entrada
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── test_api_manual.py           # Pruebas manuales
├── CHANGELOG_HU_KAN-83.md       # Detalles de implementación
├── RESUMEN_EJECUTIVO.md         # Resumen ejecutivo
├── GUIA_INTEGRACION_FRONTEND.md # Guía para frontend
└── README.md                    # Este archivo
```

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Conexión a la base de datos | `sqlite:///vendedores.db` |
| `PORT` | Puerto del servicio | `5002` |
| `FLASK_ENV` | Entorno de ejecución | `production` |
| `LOG_LEVEL` | Nivel de logs | `INFO` |

### Ejemplo `.env`
```bash
DATABASE_URL=postgresql://medisupply_user:password@localhost:5432/medisupply
PORT=5002
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

## 🐳 Docker

### Build
```bash
docker build -t vendedores-microservice .
```

### Run
```bash
docker run -p 5002:5002 \
  -e DATABASE_URL="postgresql://user:pass@db:5432/medisupply" \
  vendedores-microservice
```

### Docker Compose
```bash
docker-compose up -d
```

## 📊 Modelo de Datos

### Vendedor
```python
{
  "id": "UUID",
  "nombre": "string (1-150)",
  "apellidos": "string (1-150)",
  "correo": "string (email, único)",
  "celular": "string (10+ dígitos)",
  "telefono": "string (10+ dígitos) | null",
  "zona": "string (1-80) | null",
  "estado": "activo | inactivo",
  "usuario_creacion": "string | null",
  "fecha_creacion": "datetime",
  "usuario_actualizacion": "string | null",
  "fecha_actualizacion": "datetime"
}
```

## 🔍 Ejemplos de Uso

### cURL

```bash
# Crear vendedor
curl -X POST http://localhost:5002/vendedores \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "apellidos": "Pérez",
    "correo": "juan@example.com",
    "celular": "3001234567"
  }'

# Listar vendedores
curl http://localhost:5002/vendedores?page=1&size=10

# Obtener vendedor específico
curl http://localhost:5002/vendedores/{id}

# Actualizar vendedor
curl -X PATCH http://localhost:5002/vendedores/{id} \
  -H "Content-Type: application/json" \
  -d '{"zona": "Cali"}'
```

### Python

```python
import requests

# Crear vendedor
response = requests.post(
    'http://localhost:5002/vendedores',
    json={
        'nombre': 'Juan',
        'apellidos': 'Pérez',
        'correo': 'juan@example.com',
        'celular': '3001234567'
    }
)
vendedor = response.json()
print(vendedor)
```

## 🐛 Troubleshooting

### Error: "Faltan campos obligatorios"
**Solución**: Asegúrate de enviar nombre, apellidos, correo y celular.

### Error: "Ya existe un vendedor registrado con ese correo"
**Solución**: El correo debe ser único. Usa otro correo o actualiza el vendedor existente.

### Error: "'correo' no tiene un formato válido"
**Solución**: Verifica que el correo tenga el formato: texto@dominio.extension

### Error: "'celular' debe tener al menos 10 dígitos"
**Solución**: El celular debe contener al menos 10 números (pueden incluir espacios, guiones).

## 📞 Soporte

Para dudas o problemas:
1. Revisar [`RESUMEN_EJECUTIVO.md`](RESUMEN_EJECUTIVO.md)
2. Ver ejemplos en [`test_api_manual.py`](test_api_manual.py)
3. Ejecutar tests: `pytest test/unit/ -v`
4. Contactar al equipo de desarrollo

## 📄 Licencia

MIT License - Ver archivo LICENSE para más detalles.

## 👥 Equipo

Desarrollado por el equipo de MediSupply Backend

---

**Última actualización**: 2025-10-15
**Versión**: 2.0.0 (HU KAN-83 implementada)

