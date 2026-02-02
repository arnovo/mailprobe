#!/bin/bash
# Validación pre-PR: ejecutar antes de crear un Pull Request
# Uso: ./scripts/validate-pr.sh [base-branch]

set -e

BASE_BRANCH="${1:-main}"
CURRENT_BRANCH=$(git branch --show-current)

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Validación Pre-Pull Request        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Rama actual: ${YELLOW}$CURRENT_BRANCH${NC}"
echo -e "Base: ${YELLOW}$BASE_BRANCH${NC}"
echo ""

ERRORS=0

# ============================================
# 1. Verificar que no estamos en main
# ============================================
echo -e "${YELLOW}▶ Verificando rama...${NC}"
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo -e "${RED}✗ No puedes crear PR desde main/master${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ Rama OK: $CURRENT_BRANCH${NC}"
fi

# ============================================
# 2. Verificar commits pendientes
# ============================================
echo -e "${YELLOW}▶ Verificando commits...${NC}"
COMMITS=$(git log --oneline "$BASE_BRANCH..HEAD" 2>/dev/null | wc -l | tr -d ' ')
if [ "$COMMITS" -eq 0 ]; then
    echo -e "${RED}✗ No hay commits nuevos respecto a $BASE_BRANCH${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ $COMMITS commit(s) para incluir en PR${NC}"
    git log --oneline "$BASE_BRANCH..HEAD" | head -10
fi

# ============================================
# 3. Verificar formato de commits (Conventional Commits)
# ============================================
echo ""
echo -e "${YELLOW}▶ Verificando formato de commits...${NC}"
INVALID_COMMITS=0
while IFS= read -r commit; do
    if [ -n "$commit" ]; then
        # Verificar que empiece con tipo válido
        if ! echo "$commit" | grep -qE "^[a-f0-9]+ (feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?(!)?:"; then
            echo -e "${RED}  ✗ $commit${NC}"
            INVALID_COMMITS=$((INVALID_COMMITS + 1))
        fi
    fi
done <<< "$(git log --oneline "$BASE_BRANCH..HEAD" 2>/dev/null)"

if [ "$INVALID_COMMITS" -gt 0 ]; then
    echo -e "${RED}✗ $INVALID_COMMITS commit(s) no siguen Conventional Commits${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ Todos los commits siguen Conventional Commits${NC}"
fi

# ============================================
# 4. Verificar tests backend
# ============================================
echo ""
echo -e "${YELLOW}▶ Ejecutando tests backend...${NC}"
cd backend
PYTHON_CMD="python3"
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
fi

if $PYTHON_CMD -m pytest tests/ -q --tb=short 2>&1 | tail -5; then
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}✓ Tests backend OK${NC}"
    else
        echo -e "${RED}✗ Tests backend fallaron${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗ Error ejecutando tests${NC}"
    ERRORS=$((ERRORS + 1))
fi
cd ..

# ============================================
# 5. Verificar linting backend
# ============================================
echo ""
echo -e "${YELLOW}▶ Verificando linting backend...${NC}"
cd backend
if $PYTHON_CMD -m ruff check app/ --quiet; then
    echo -e "${GREEN}✓ Ruff OK${NC}"
else
    echo -e "${RED}✗ Ruff encontró errores${NC}"
    ERRORS=$((ERRORS + 1))
fi
cd ..

# ============================================
# 6. Verificar TypeScript frontend
# ============================================
echo ""
echo -e "${YELLOW}▶ Verificando TypeScript frontend...${NC}"
cd frontend
if npx tsc --noEmit --skipLibCheck 2>/dev/null; then
    echo -e "${GREEN}✓ TypeScript OK${NC}"
else
    echo -e "${RED}✗ Errores de TypeScript${NC}"
    ERRORS=$((ERRORS + 1))
fi
cd ..

# ============================================
# 7. Verificar que no hay secretos
# ============================================
echo ""
echo -e "${YELLOW}▶ Verificando secretos...${NC}"
SECRETS_PATTERN='(api_key|apikey|password|secret|token|private_key)[[:space:]]*[=:][[:space:]]*["\x27][^"\x27]{8,}'
if git diff "$BASE_BRANCH..HEAD" | grep -iE "$SECRETS_PATTERN" > /dev/null 2>&1; then
    echo -e "${RED}✗ Posibles secretos detectados en los cambios${NC}"
    echo -e "${YELLOW}  Revisa: git diff $BASE_BRANCH..HEAD${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ Sin secretos detectados${NC}"
fi

# ============================================
# Resumen
# ============================================
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}✗ Validación fallida: $ERRORS error(es)${NC}"
    echo -e "${YELLOW}Corrige los errores antes de crear el PR${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Validación exitosa - listo para crear PR${NC}"
    echo ""
    echo -e "Comando sugerido:"
    echo -e "${YELLOW}gh pr create --title \"...\" --body \"...\"${NC}"
    exit 0
fi
