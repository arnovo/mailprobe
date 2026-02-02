#!/bin/bash
# Stop all development services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop background worker if exists
if [ -f ".worker.pid" ]; then
  WORKER_PID=$(cat .worker.pid)
  if kill -0 "$WORKER_PID" 2>/dev/null; then
    echo "Stopping Celery worker (PID: $WORKER_PID)..."
    kill "$WORKER_PID" 2>/dev/null || true
    sleep 1
  fi
  rm -f .worker.pid
fi

echo "Stopping Docker services..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

echo "Done. All services stopped."
