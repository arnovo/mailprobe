#!/bin/bash
# Para todos los servicios de desarrollo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parar worker en background si existe
if [ -f ".worker.pid" ]; then
  WORKER_PID=$(cat .worker.pid)
  if kill -0 "$WORKER_PID" 2>/dev/null; then
    echo "Parando worker Celery (PID: $WORKER_PID)..."
    kill "$WORKER_PID" 2>/dev/null || true
    sleep 1
  fi
  rm -f .worker.pid
fi

echo "Parando servicios Docker..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

echo "Listo. Todos los servicios parados."
