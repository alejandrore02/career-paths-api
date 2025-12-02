#!/bin/bash
# Script de inicio para aplicación Talent Management
# Ejecuta migraciones automáticamente antes de iniciar el servidor

set -e

echo "🔄 Ejecutando migraciones de Alembic..."
alembic upgrade head

echo "✅ Migraciones completadas"
echo "🚀 Iniciando servidor FastAPI..."

# Si se pasa --reload como argumento, iniciar en modo desarrollo
if [ "$1" = "--reload" ] || [ "$RELOAD" = "true" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
