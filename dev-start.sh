#!/bin/bash
# Script para desarrollo - detecta automáticamente Mac vs Linux
#
# Mac (Darwin): Worker corre fuera de Docker (puerto 25 bloqueado en Docker)
# Linux: Todo corre en Docker (puerto 25 funciona)
#
# Uso:
#   ./dev-start.sh          # Worker en primer plano (solo Mac)
#   ./dev-start.sh -d       # Worker en segundo plano (solo Mac)
#   ./dev-start.sh --bg     # Worker en segundo plano (solo Mac)

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Detectar sistema operativo
OS="$(uname)"
IS_MAC=false
if [[ "$OS" == "Darwin" ]]; then
  IS_MAC=true
fi

# Parámetros
BACKGROUND=false
for arg in "$@"; do
  case $arg in
    -d|--bg|--background)
      BACKGROUND=true
      shift
      ;;
  esac
done

echo "=== Mailprobe - Modo Desarrollo ==="
if [ "$IS_MAC" = true ]; then
  echo -e "${CYAN}Detectado: macOS - Worker correrá fuera de Docker${NC}"
else
  echo -e "${CYAN}Detectado: Linux - Todo corre en Docker${NC}"
fi
echo ""

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Comando docker compose
if [ "$IS_MAC" = true ]; then
  # Mac: usa override de dev (worker deshabilitado)
  DC="docker compose -f docker-compose.yml -f docker-compose.dev.yml"
else
  # Linux: usa solo el yml base (incluye worker)
  DC="docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile all"
fi

# 1. Parar servicios anteriores si existen
echo -e "${YELLOW}[1/4] Limpiando servicios anteriores...${NC}"
$DC down 2>/dev/null || true
# También parar worker local si existe
if [ -f ".worker.pid" ]; then
  WORKER_PID=$(cat .worker.pid)
  kill "$WORKER_PID" 2>/dev/null || true
  rm -f .worker.pid
fi

# 2. Arrancar servicios de Docker
echo -e "${YELLOW}[2/4] Arrancando servicios en Docker (con hot reload)...${NC}"
if [ "$IS_MAC" = true ]; then
  $DC up -d --build
else
  # Linux: incluir worker con --profile linux
  docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile linux up -d --build
fi

# Esperar a que estén listos
echo "Esperando a que los servicios estén listos..."
sleep 3

# 3. Verificar que Redis esté accesible
echo -e "${YELLOW}[3/4] Verificando conexión a Redis...${NC}"
until docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
  echo "  Esperando Redis..."
  sleep 1
done
echo -e "${GREEN}  Redis OK${NC}"

# 4. Arrancar worker
echo -e "${YELLOW}[4/4] Configurando Worker...${NC}"
echo ""
echo -e "${GREEN}=== Servicios Docker ===${NC}"
echo "  - Postgres:  localhost:5432"
echo "  - Redis:     localhost:6379"
echo "  - Backend:   http://localhost:8000"
echo "  - Frontend:  http://localhost:3002"
echo ""

if [ "$IS_MAC" = true ]; then
  # Mac: worker fuera de Docker
  cd backend
  source .venv/bin/activate

  if [ "$BACKGROUND" = true ]; then
    # Segundo plano
    WORKER_LOG="$SCRIPT_DIR/worker.log"
    echo -e "${GREEN}=== Worker Celery (Mac - background) ===${NC}"
    echo "  Logs en: $WORKER_LOG"
    echo "  Para parar: ./dev-stop.sh"
    echo ""
    nohup celery -A app.tasks.celery_app worker -l info > "$WORKER_LOG" 2>&1 &
    WORKER_PID=$!
    echo $WORKER_PID > "$SCRIPT_DIR/.worker.pid"
    echo -e "${GREEN}Worker arrancado (PID: $WORKER_PID)${NC}"
    echo ""
    echo "Ver logs: tail -f worker.log"
  else
    # Primer plano
    echo -e "${GREEN}=== Worker Celery (Mac - foreground) ===${NC}"
    echo "  El worker corre en Mac para tener acceso al puerto 25 (SMTP)"
    echo "  Presiona Ctrl+C para parar el worker"
    echo ""
    echo "-------------------------------------------"
    exec celery -A app.tasks.celery_app worker -l info
  fi
else
  # Linux: worker ya está en Docker
  echo -e "${GREEN}=== Worker Celery (Docker) ===${NC}"
  echo "  Worker corriendo en Docker con acceso al puerto 25"
  echo "  Ver logs: docker compose logs -f worker"
  echo ""
  echo -e "${GREEN}Todo listo.${NC}"
fi
