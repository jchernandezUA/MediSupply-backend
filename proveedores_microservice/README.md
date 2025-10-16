# Microservicio de Proveedores - MediSupply

Microservicio encargado de la gestión de proveedores médicos para el sistema MediSupply. Permite el registro de proveedores con sus respectivas certificaciones sanitarias.

## 🚀 Funcionalidades

### ✅ Implementadas (HU KAN-91)

- **Registro de Proveedores**: Registro completo de nuevos proveedores con validación de datos
- **Gestión de Certificaciones**: Upload y almacenamiento de certificaciones sanitarias (PDF, JPG, PNG)
- **Validación de NIT**: Verificación de unicidad y formato correcto del NIT
- **Estados de Proveedor**: Gestión de estados Activo/Inactivo
- **Health Check**: Endpoint para verificar el estado del servicio

### 🔄 En Desarrollo

- Consulta de proveedores
- Actualización de información
- Búsqueda y filtros
- Gestión de certificaciones vencidas

## 🛠️ Tecnologías

- **Framework**: Flask 2.3.3
- **Base de Datos**: PostgreSQL (desarrollo) / SQLite (testing)
- **ORM**: SQLAlchemy 2.0.21
- **Validación**: Marshmallow + validadores customizados
- **Testing**: pytest con 94% de cobertura
- **Upload**: Werkzeug para manejo seguro de archivos

## 📋 Requisitos

- Python 3.8+
- PostgreSQL 12+ (para desarrollo)
- pip / pipenv / poetry

## 🏃‍♂️ Ejecución Local

### 1. Clonar y configurar el proyecto

```bash
# Clonar el repositorio
git clone <repo-url>
cd MediSupply-backend/proveedores_microservice

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear archivo `.env` en la raíz del microservicio:

```properties
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/medisupply
SECRET_KEY=supersecretkey
FLASK_DEBUG=true
```

### 3. Configurar base de datos

```sql
-- Conectar a PostgreSQL y crear la base de datos
CREATE DATABASE medisupply;
```

### 4. Ejecutar el microservicio

```bash
# Iniciar el servidor de desarrollo
python run.py
```

El servidor estará disponible en:
- http://localhost:5006
- http://127.0.0.1:5006

## 🧪 Ejecutar Tests

### Tests completos con coverage

```bash
# Ejecutar toda la suite de tests
python -m pytest tests/ -v

# Con reporte de coverage
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing -v

# Ver reporte HTML
# Abrir htmlcov/index.html en el navegador
```

### Tests específicos

```bash
# Tests de un módulo específico
python -m pytest tests/test_proveedor.py -v

# Test específico
python -m pytest tests/test_proveedor.py::TestProveedorEndpoints::test_registrar_proveedor_exitoso -v
```

### Cobertura actual

- **Coverage Total**: 94%
- **Tests**: 48 pasando
- **Módulos cubiertos**: Modelos, Servicios, Endpoints, Validadores

## 📁 Estructura del Proyecto

```
proveedores_microservice/
├── app/
│   ├── __init__.py          # Factory de la aplicación Flask
│   ├── config.py            # Configuraciones (Config, TestingConfig)
│   ├── extensions.py        # Extensiones (SQLAlchemy, Marshmallow)
│   ├── models/
│   │   └── proveedor.py     # Modelos Proveedor y Certificacion
│   ├── routes/
│   │   └── proveedores_bp.py # Endpoints REST
│   ├── services/
│   │   └── proveedor_service.py # Lógica de negocio
│   └── utils/
│       └── validators.py    # Validadores de datos y archivos
├── tests/                   # Suite de tests con 94% coverage
├── uploads/                 # Archivos subidos (no versionado)
├── requirements.txt         # Dependencias
├── pytest.ini             # Configuración de pytest
├── run.py                  # Punto de entrada
└── README.md               # Este archivo
```

## 🚦 Health Check

```bash
# Verificar que el servicio está corriendo
curl http://localhost:5006/api/proveedores/health

# Respuesta esperada:
{
  "estado": "activo",
  "servicio": "Proveedores Microservice",
  "timestamp": "2024-XX-XX XX:XX:XX"
}
```

## 🔧 Configuración de Desarrollo

### Variables de entorno disponibles

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `sqlite:///proveedores.db` |
| `SECRET_KEY` | Clave secreta de Flask | `clave-secreta` |
| `FLASK_DEBUG` | Modo debug | `False` |
| `TESTING` | Modo testing (usa :memory:) | `False` |

### Configuración de uploads

- **Tamaño máximo**: 5MB por archivo
- **Formatos permitidos**: PDF, JPG, JPEG, PNG
- **Directorio**: `uploads/certificaciones/{proveedor_id}/`

## 📚 Documentación Adicional

- [Contratos de API](wiki/contratos-api.md)
- [Guía de Testing](wiki/testing.md)
- [Arquitectura](wiki/arquitectura.md)

## 🤝 Contribución

1. Crear rama desde `develop`
2. Implementar funcionalidad
3. Asegurar 85%+ de coverage en tests
4. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](../LICENSE).