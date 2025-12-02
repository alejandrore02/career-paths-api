FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Paquetes del sistema necesarios (compilación, postgres client, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 2. Copiamos solo lo necesario para resolver deps
COPY pyproject.toml README.md ./
COPY app ./app

# 3. Instalamos dependencias del proyecto (con dev dependencies)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[dev]"

# 4. Copiamos el resto del código (alembic, tests, etc.)
COPY . .

EXPOSE 8000

# 5. Comando por defecto (ejecuta migraciones automáticamente)
CMD ["./scripts/start.sh"]