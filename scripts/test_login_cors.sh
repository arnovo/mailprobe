#!/bin/sh
# Prueba login y CORS. Ejecutar con el backend arriba (docker compose up -d backend).

BASE="${1:-http://localhost:8000}"

echo "=== 1. Health ==="
curl -s "$BASE/health" | head -1
echo ""

echo "=== 2. Login (POST) ==="
curl -s -X POST "$BASE/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme"}' | head -c 200
echo ""

echo ""
echo "=== 3. Preflight OPTIONS (simula navegador desde http://localhost:3001) ==="
curl -s -D - -o /dev/null -X OPTIONS "$BASE/v1/auth/login" \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
echo "Debe incluir: Access-Control-Allow-Origin: http://localhost:3001"
