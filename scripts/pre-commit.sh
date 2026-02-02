#!/bin/bash
# Pre-commit hook para Email Finder MVP
# Ejecuta linters, type-check, detección de secretos y tests

set -e

echo "🔍 Ejecutando pre-commit hooks..."

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detectar archivos staged
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
BACKEND_CHANGED=$(echo "$STAGED_FILES" | grep "^backend/" || true)
FRONTEND_CHANGED=$(echo "$STAGED_FILES" | grep -E "^frontend/src/.*\.(ts|tsx|js|jsx)$" || true)

# Código Python del backend (app/, no tests/) - requiere añadir tests
BACKEND_CODE_PY=$(echo "$STAGED_FILES" | grep -E "^backend/app/.*\.py$" || true)

# ============================================
# 1. Detección de secretos
# ============================================
echo -e "${YELLOW}▶ Verificando secretos...${NC}"
SECRETS_PATTERN='(api_key|apikey|api-key|password|passwd|secret|token|private_key|privatekey|credential|auth_token|access_token|refresh_token)[[:space:]]*[=:][[:space:]]*["\x27][^"\x27]{8,}'

if git diff --cached --diff-filter=ACM -U0 | grep -iE "$SECRETS_PATTERN" > /dev/null 2>&1; then
    echo -e "${RED}✗ Posible secreto detectado en el código${NC}"
    echo -e "${RED}  Revisa las líneas con: git diff --cached${NC}"
    echo -e "${YELLOW}  Si es un falso positivo, usa: git commit --no-verify${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Sin secretos detectados${NC}"

# ============================================
# 2. Verificar tamaño de archivos (max 500KB)
# ============================================
MAX_FILE_SIZE=512000  # 500KB en bytes
echo -e "${YELLOW}▶ Verificando tamaño de archivos...${NC}"

for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        FILE_SIZE=$(wc -c < "$file" 2>/dev/null || echo 0)
        if [ "$FILE_SIZE" -gt "$MAX_FILE_SIZE" ]; then
            echo -e "${RED}✗ Archivo demasiado grande: $file ($(($FILE_SIZE / 1024))KB > 500KB)${NC}"
            exit 1
        fi
    fi
done
echo -e "${GREEN}✓ Tamaño de archivos OK${NC}"

# ============================================
# 3. Linter Backend (ruff) - solo archivos staged
# ============================================
if [ -n "$BACKEND_CHANGED" ]; then
    echo -e "${YELLOW}▶ Ejecutando ruff (backend)...${NC}"
    cd backend
    
    # Extraer solo los archivos .py staged
    BACKEND_PY_FILES=$(echo "$BACKEND_CHANGED" | grep '\.py$' | sed 's|^backend/||' || true)
    
    if [ -n "$BACKEND_PY_FILES" ]; then
        # Use venv python if available
        PYTHON_CMD="python3"
        if [ -f ".venv/bin/python" ]; then
            PYTHON_CMD=".venv/bin/python"
        fi
        if echo "$BACKEND_PY_FILES" | xargs $PYTHON_CMD -m ruff check --fix; then
            echo -e "${GREEN}✓ ruff OK${NC}"
        else
            echo -e "${RED}✗ ruff encontró errores${NC}"
            cd ..
            exit 1
        fi
    fi
    cd ..
fi

# ============================================
# 4. Linter Frontend (eslint) - solo archivos staged
# ============================================
if [ -n "$FRONTEND_CHANGED" ]; then
    echo -e "${YELLOW}▶ Ejecutando eslint (frontend)...${NC}"
    cd frontend
    
    # Extraer rutas relativas al frontend
    FRONTEND_FILES=$(echo "$FRONTEND_CHANGED" | sed 's|^frontend/||')
    
    if echo "$FRONTEND_FILES" | xargs npx eslint --max-warnings 0; then
        echo -e "${GREEN}✓ eslint OK${NC}"
    else
        echo -e "${RED}✗ eslint encontró errores${NC}"
        cd ..
        exit 1
    fi
    cd ..
fi

# ============================================
# 5. TypeScript type-check (frontend)
# ============================================
if [ -n "$FRONTEND_CHANGED" ]; then
    echo -e "${YELLOW}▶ Verificando tipos TypeScript...${NC}"
    cd frontend
    
    if npx tsc --noEmit --skipLibCheck 2>&1 | head -20; then
        # tsc retorna 0 si no hay errores
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo -e "${GREEN}✓ TypeScript OK${NC}"
        else
            echo -e "${RED}✗ Errores de TypeScript${NC}"
            cd ..
            exit 1
        fi
    fi
    cd ..
fi

# ============================================
# 6. Tests Backend (pytest)
# ============================================
if [ -n "$BACKEND_CHANGED" ]; then
    echo -e "${YELLOW}▶ Ejecutando tests (backend)...${NC}"
    cd backend
    # Use venv python if available
    PYTHON_CMD="python3"
    if [ -f ".venv/bin/python" ]; then
        PYTHON_CMD=".venv/bin/python"
    fi
    if $PYTHON_CMD -m pytest tests/ -x -q --tb=short 2>&1 | tail -20; then
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo -e "${GREEN}✓ tests OK${NC}"
        else
            echo -e "${RED}✗ tests fallaron${NC}"
            cd ..
            exit 1
        fi
    fi
    cd ..
fi

# ============================================
# 7. Verificar que se añadieron tests nuevos
# ============================================
# Solo aplica si hay cambios en código Python de backend/app/ (no tests, no configs)
if [ -n "$BACKEND_CODE_PY" ] && [ -z "$SKIP_TEST_COUNT" ]; then
    echo -e "${YELLOW}▶ Verificando cantidad de tests...${NC}"
    cd backend
    
    # Use venv python if available
    PYTHON_CMD="python3"
    if [ -f ".venv/bin/python" ]; then
        PYTHON_CMD=".venv/bin/python"
    fi
    
    # Contar tests en estado actual (staged)
    TESTS_STAGED=$($PYTHON_CMD -m pytest tests/ --collect-only -q 2>/dev/null | grep -c "test_" || echo 0)
    
    # Detectar archivos de test nuevos (añadidos, no en HEAD)
    cd ..
    NEW_TEST_FILES=$(git diff --cached --name-only --diff-filter=A | grep "^backend/tests/test_.*\.py$" || true)
    cd backend
    
    if [ -n "$NEW_TEST_FILES" ]; then
        # Hay archivos de test nuevos, contar cuántos tests aportan
        NEW_TESTS=0
        for f in $NEW_TEST_FILES; do
            # Extraer ruta relativa a backend/
            REL_PATH=$(echo "$f" | sed 's|^backend/||')
            COUNT=$($PYTHON_CMD -m pytest "$REL_PATH" --collect-only -q 2>/dev/null | grep -c "test_" || echo 0)
            NEW_TESTS=$((NEW_TESTS + COUNT))
        done
        if [ "$NEW_TESTS" -gt 0 ]; then
            echo -e "${GREEN}✓ +$NEW_TESTS tests nuevos en archivos nuevos${NC}"
            cd ..
        else
            echo -e "${RED}✗ Archivos de test nuevos pero sin tests válidos${NC}"
            cd ..
            exit 1
        fi
    else
        # No hay archivos nuevos, comparar con HEAD
        git stash push --keep-index --quiet 2>/dev/null || true
        
        cd ..
        git checkout HEAD -- backend/tests/ 2>/dev/null || true
        cd backend
        TESTS_HEAD=$($PYTHON_CMD -m pytest tests/ --collect-only -q 2>/dev/null | grep -c "test_" || echo 0)
        
        cd ..
        git checkout --quiet -- backend/tests/ 2>/dev/null || true
        git stash pop --quiet 2>/dev/null || true
        
        if [ "$TESTS_STAGED" -le "$TESTS_HEAD" ]; then
            echo -e "${RED}✗ No se añadieron tests nuevos ($TESTS_HEAD → $TESTS_STAGED)${NC}"
            echo -e "${YELLOW}  Para forzar: SKIP_TEST_COUNT=1 git commit ...${NC}"
            echo -e "${YELLOW}  O usa: git commit --no-verify${NC}"
            exit 1
        else
            DIFF=$((TESTS_STAGED - TESTS_HEAD))
            echo -e "${GREEN}✓ +$DIFF tests nuevos ($TESTS_HEAD → $TESTS_STAGED)${NC}"
        fi
    fi
fi

echo -e "${GREEN}✅ Pre-commit completado${NC}"
