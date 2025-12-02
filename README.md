# Career Paths API - Talent Management System

API backend en **Python + FastAPI** para gestionar evaluaciones 360°, evaluaciones de habilidades procesadas con IA y recomendaciones de senderos de carrera.

## 🚀 Características

- **Evaluaciones 360°**: Gestión completa de evaluaciones de desempeño
- **Skills Assessment con IA**: Análisis de habilidades mediante inteligencia artificial
- **Career Paths**: Recomendaciones personalizadas de desarrollo profesional
- **Arquitectura escalable**: Diseñada para soportar miles de usuarios concurrentes
- **Resiliente**: Manejo robusto de errores y circuit breakers para servicios externos
- **Observable**: Logging estructurado, métricas y health checks

## 📋 Requisitos

- Python 3.12+
- PostgreSQL 15+
- Docker y docker-compose (opcional)

## 🛠️ Quick Start

### Paso 1: Clonar el repositorio

```bash
git clone <repository-url>
cd career-paths-api
```

### Paso 2: Elegir método de instalación

#### Opción A: Docker Compose (recomendado - más rápido)

```bash
# Inicia la aplicación con migraciones automáticas
cp .env.example .env
docker-compose up --build

# Las migraciones se ejecutan automáticamente antes de iniciar el servidor
```

La API estará disponible en <http://localhost:8000>

**✅ Listo!** Pasa a la sección [Documentación de la API](#-documentación-de-la-api) para explorar los endpoints.

---

#### Opción B: Desarrollo local (con uv o pip)

**1. Crear entorno virtual e instalar dependencias**

Con uv (recomendado - más rápido):

```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Crear entorno virtual e instalar dependencias
uv venv
source .venv/bin/activate 
uv sync
uv pip install -e ".[dev]"
```

Con pip tradicional:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

**2. Configurar variables de entorno**

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env si necesitas ajustar valores
```

**Variables críticas:**

- `DATABASE_URL`: URL de conexión a PostgreSQL
- `USE_AI_DUMMY_MODE=true`: Usar respuestas simuladas de IA (desarrollo)
- Ver [docs/ENV_CONFIG.md](docs/ENV_CONFIG.md) para detalles completos

**3. Iniciar PostgreSQL** (si no está corriendo):

```bash
docker run -d \
  --name talent-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=talent_management \
  -p 5432:5432 \
  postgres:15-alpine
```

**4. Iniciar la aplicación** (migraciones automáticas):

```bash
# Las migraciones se ejecutan automáticamente al iniciar
./scripts/start.sh --reload

# O manualmente con uvicorn (debes ejecutar migraciones antes)
alembic upgrade head && uvicorn app.main:app --reload
```

La API estará disponible en <http://localhost:8000>

## 📚 Documentación de la API

Una vez iniciada la aplicación, accede a:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## 🗂️ Estructura del Proyecto

```text
talent-management/
├── app/
│   ├── api/v1/              # Endpoints de la API
│   ├── core/                # Configuración, logging, errors
│   ├── db/                  # Modelos, repositorios, UoW
│   ├── domain/              # Lógica de dominio
│   ├── integrations/        # Clientes externos (AI, HTTP)
│   ├── schemas/             # DTOs Pydantic
│   ├── services/            # Servicios de aplicación
│   └── main.py              # Punto de entrada FastAPI
├── tests/                   # Pruebas
├── alembic/                 # Migraciones de BD
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

Consultar [ARCHITECTURE.md](./docs/ARCHITECTURE.md) para más detalles sobre la arquitectura.
Consultar [flows.md](./docs/flows.md) para más detalles sobre los flujos.
COnsultar [planteamiento.md](./docs/planteamiento.md) para revisar preguntas iniciales para maquetar el proyecto.
## 🔌 API Endpoints Principales

### Health Checks

- `GET /health` - Health check básico
- `GET /ready` - Readiness check (verifica BD)

### Evaluaciones 360°

- `POST /api/v1/evaluations` - Crear evaluación
- `GET /api/v1/evaluations?user_id={id}&cycle_id={id}` - Listar evaluaciones
- `GET /api/v1/evaluations/{id}` - Detalle de evaluación
- `POST /api/v1/evaluations/{id}/process` - Procesar y agregar scores

### Skills Assessments (IA)

- `POST /api/v1/skills-assessments` - Generar assessment con IA
- `GET /api/v1/skills-assessments/{user_id}/latest` - Último assessment del usuario
- `GET /api/v1/skills-assessments/{id}` - Detalle de assessment

### Career Paths (IA)

- `POST /api/v1/career-paths` - Generar career paths con IA
- `GET /api/v1/career-paths/{user_id}` - Listar paths del usuario
- `GET /api/v1/career-paths/{path_id}/steps` - Detalle con pasos

###  (Roles, Skills, Users, Cycles)

- `GET/POST /api/v1/roles` - Gestión de roles
- `GET/POST /api/v1/skills` - Gestión de habilidades
- `GET/POST /api/v1/users` - Gestión de usuarios
- `GET/POST /api/v1/evaluation-cycles` - Gestión de ciclos


## 🧪 Testing

```bash
# Todos los tests (Docker - recomendado)
./scripts/run_tests.sh all

# Solo tests unitarios (sin BD)
./scripts/run_tests.sh unit

# Solo tests de integración
./scripts/run_tests.sh integration

# Solo tests E2E
./scripts/run_tests.sh e2e

# Con reporte de cobertura
./scripts/run_tests.sh coverage
```

**Cobertura actual: 76% (58 tests)** ✅

Ver [tests/README.md](tests/README.md) para detalles de la estrategia de testing.

## 🔧 Desarrollo

### Migraciones de base de datos

```bash
# Crear nueva migración (después de cambios en modelos)
alembic revision --autogenerate -m "Descripción del cambio"

# Las migraciones se aplican automáticamente al iniciar la app
# Para aplicar manualmente (si es necesario):
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

## 🧠 Modelos de IA utilizados

Además de la arquitectura y el código, este repositorio incluye **instrucciones personalizadas para asistentes de IA** ubicadas en:

```text
.github/chatmodes/
```

### **1. Claude 4.5 — GitHub Edition**

Utilizado para:

- Implementación de arquitectura (capas, servicios, repositorios, UoW, clientes IA).
- Estructuración de componentes del proyecto siguiendo patrones modernos (Clean Architecture, DDD-lite).
- Propuestas de flujos de negocio, validación cruzada y consistencia entre módulos.
- Revisión crítica de decisiones técnicas, organización del código y convenciones estructurales.
- Generación de bases para documentos como `ARCHITECTURE.md` y `flows.md`.

Este modelo sirvió como maquetador principal.

---

### **2. ChatGPT Mini 5 — OpenAI**

Utilizado para:

- Refinar las plantillas generadas por Claude y convertirlas en código funcional.
- Crear boilerplate de archivos (`routers`, `services`, `repositories`, `schemas`, `integration clients`).
- Generar documentación limpia y clara para desarrolladores (README, guías de testing, instructivos).
- Maquetar scripts y automatización del flujo de desarrollo.
- Unificar criterios, estilo de código e integraciones entre módulos.

