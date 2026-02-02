#!/bin/bash
# Development script - automatically detects Mac vs Linux
#
# Mac (Darwin): Worker runs outside Docker (port 25 blocked in Docker)
# Linux: Everything runs in Docker (port 25 works)
#
# Usage:
#   ./dev-start.sh          # Worker in foreground (Mac only)
#   ./dev-start.sh -d       # Worker in background (Mac only)
#   ./dev-start.sh --bg     # Worker in background (Mac only)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Detect operating system
OS="$(uname)"
IS_MAC=false
if [[ "$OS" == "Darwin" ]]; then
  IS_MAC=true
fi

# Parameters
BACKGROUND=false
for arg in "$@"; do
  case $arg in
    -d|--bg|--background)
      BACKGROUND=true
      shift
      ;;
  esac
done

echo "=== Mailprobe - Development Mode ==="
if [ "$IS_MAC" = true ]; then
  echo -e "${CYAN}Detected: macOS - Worker will run outside Docker${NC}"
else
  echo -e "${CYAN}Detected: Linux - Everything runs in Docker${NC}"
fi
echo ""

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Docker compose command
if [ "$IS_MAC" = true ]; then
  # Mac: use dev override (worker disabled)
  DC="docker compose -f docker-compose.yml -f docker-compose.dev.yml"
else
  # Linux: use base yml only (includes worker)
  DC="docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile all"
fi

# 1. Stop previous services if any
echo -e "${YELLOW}[1/4] Cleaning up previous services...${NC}"
$DC down 2>/dev/null || true
# Also stop local worker if exists
if [ -f ".worker.pid" ]; then
  WORKER_PID=$(cat .worker.pid)
  kill "$WORKER_PID" 2>/dev/null || true
  rm -f .worker.pid
fi

# 2. Start Docker services
echo -e "${YELLOW}[2/4] Starting Docker services (with hot reload)...${NC}"
if [ "$IS_MAC" = true ]; then
  $DC up -d --build
else
  # Linux: include worker with --profile linux
  docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile linux up -d --build
fi

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 3

# 3. Verify Redis is accessible
echo -e "${YELLOW}[3/4] Verifying Redis connection...${NC}"
until docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
  echo "  Waiting for Redis..."
  sleep 1
done
echo -e "${GREEN}  Redis OK${NC}"

# 4. Start worker
echo -e "${YELLOW}[4/4] Configuring Worker...${NC}"
echo ""
echo -e "${GREEN}=== Docker Services ===${NC}"
echo "  - Postgres:  localhost:5432"
echo "  - Redis:     localhost:6379"
echo "  - Backend:   http://localhost:8000"
echo "  - Frontend:  http://localhost:3002"
echo ""

if [ "$IS_MAC" = true ]; then
  # Mac: worker outside Docker
  cd backend
  source .venv/bin/activate

  if [ "$BACKGROUND" = true ]; then
    # Background mode
    WORKER_LOG="$SCRIPT_DIR/worker.log"
    echo -e "${GREEN}=== Celery Worker (Mac - background) ===${NC}"
    echo "  Logs at: $WORKER_LOG"
    echo "  To stop: ./dev-stop.sh"
    echo ""
    nohup celery -A app.tasks.celery_app worker -l info > "$WORKER_LOG" 2>&1 &
    WORKER_PID=$!
    echo $WORKER_PID > "$SCRIPT_DIR/.worker.pid"
    echo -e "${GREEN}Worker started (PID: $WORKER_PID)${NC}"
    echo ""
    echo "View logs: tail -f worker.log"
  else
    # Foreground mode
    echo -e "${GREEN}=== Celery Worker (Mac - foreground) ===${NC}"
    echo "  Worker runs on Mac to have port 25 (SMTP) access"
    echo "  Press Ctrl+C to stop the worker"
    echo ""
    echo "-------------------------------------------"
    exec celery -A app.tasks.celery_app worker -l info
  fi
else
  # Linux: worker already in Docker
  echo -e "${GREEN}=== Celery Worker (Docker) ===${NC}"
  echo "  Worker running in Docker with port 25 access"
  echo "  View logs: docker compose logs -f worker"
  echo ""
  echo -e "${GREEN}All ready.${NC}"
fi
