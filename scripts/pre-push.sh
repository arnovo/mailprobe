#!/bin/bash
# Pre-push hook: validación ligera antes de push
# Para validación completa de PR, usar: ./scripts/validate-pr.sh

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Ejecutando pre-push hooks..."

# Obtener rama actual
CURRENT_BRANCH=$(git branch --show-current)

# ============================================
# 1. Verificar que no es push directo a main
# ============================================
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    # Permitir push a main solo si es merge/fast-forward
    # Bloquear commits directos
    LOCAL_COMMITS=$(git log origin/main..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')
    if [ "$LOCAL_COMMITS" -gt 0 ]; then
        echo -e "${YELLOW}⚠ Push a main con $LOCAL_COMMITS commit(s) locales${NC}"
        echo -e "${YELLOW}  Considera usar una rama y PR${NC}"
        # No bloqueamos, solo advertimos
    fi
fi

# ============================================
# 2. Verificar formato de commits recientes
# ============================================
echo -e "${YELLOW}▶ Verificando commits...${NC}"
INVALID=0
while IFS= read -r commit; do
    if [ -n "$commit" ]; then
        if ! echo "$commit" | grep -qE "^[a-f0-9]+ (feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?(!)?:"; then
            echo -e "${RED}  ✗ $commit${NC}"
            INVALID=$((INVALID + 1))
        fi
    fi
done <<< "$(git log @{push}..HEAD --oneline 2>/dev/null || git log origin/$CURRENT_BRANCH..HEAD --oneline 2>/dev/null || echo '')"

if [ "$INVALID" -gt 0 ]; then
    echo -e "${RED}✗ $INVALID commit(s) no siguen Conventional Commits${NC}"
    echo -e "${YELLOW}  Para forzar: git push --no-verify${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Pre-push OK${NC}"
