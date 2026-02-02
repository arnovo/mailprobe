#!/bin/bash
# =============================================================================
# validate.sh - Run all project validations
# =============================================================================
# Usage: ./validate.sh [--fix] [--skip-tests] [--skip-build]
#
# Options:
#   --fix         Auto-fix linter issues where possible
#   --skip-tests  Skip running tests (faster)
#   --skip-build  Skip frontend build check
#   --backend     Only validate backend
#   --frontend    Only validate frontend
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# GIT HOOKS SYNC
# =============================================================================

# Función para instalar/actualizar un hook
install_hook() {
    local HOOK_NAME=$1
    local HOOK_SOURCE="scripts/${HOOK_NAME}.sh"
    local HOOK_DEST=".git/hooks/${HOOK_NAME}"
    
    if [ -f "$HOOK_SOURCE" ]; then
        NEEDS_INSTALL=false
        
        if [ ! -f "$HOOK_DEST" ]; then
            NEEDS_INSTALL=true
            echo -e "${YELLOW}→ ${HOOK_NAME} hook no instalado${NC}"
        elif ! diff -q "$HOOK_SOURCE" "$HOOK_DEST" > /dev/null 2>&1; then
            NEEDS_INSTALL=true
            echo -e "${YELLOW}→ ${HOOK_NAME} hook desactualizado${NC}"
        fi
        
        if [ "$NEEDS_INSTALL" = true ]; then
            cp "$HOOK_SOURCE" "$HOOK_DEST"
            chmod +x "$HOOK_DEST"
            echo -e "${GREEN}✓ ${HOOK_NAME} hook instalado/actualizado${NC}"
        fi
    fi
}

# Instalar hooks
install_hook "pre-commit"
install_hook "pre-push"

# Parse arguments
FIX_MODE=""
SKIP_TESTS=false
SKIP_BUILD=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
    case $arg in
        --fix)
            FIX_MODE="--fix"
            ;;
        --skip-tests)
            SKIP_TESTS=true
            ;;
        --skip-build)
            SKIP_BUILD=true
            ;;
        --backend)
            BACKEND_ONLY=true
            ;;
        --frontend)
            FRONTEND_ONLY=true
            ;;
    esac
done

# Track failures
FAILED=0

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    PROJECT VALIDATION                            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# =============================================================================
# BACKEND VALIDATION
# =============================================================================
if [ "$FRONTEND_ONLY" = false ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  BACKEND                                                          ${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check if backend directory exists
    if [ ! -d "backend" ]; then
        echo -e "${RED}✗ Backend directory not found${NC}"
        exit 1
    fi
    
    cd backend
    
    # Activate venv if exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate 2>/dev/null || true
    fi
    
    # 1. Ruff linter
    echo -e "\n${YELLOW}→ Running Ruff linter...${NC}"
    if python -m ruff check app/ tests/ $FIX_MODE; then
        echo -e "${GREEN}✓ Ruff: All checks passed${NC}"
    else
        echo -e "${RED}✗ Ruff: Linter errors found${NC}"
        FAILED=1
    fi
    
    # 2. Ruff format check
    echo -e "\n${YELLOW}→ Checking code formatting (Ruff)...${NC}"
    if python -m ruff format --check app/ tests/ 2>/dev/null; then
        echo -e "${GREEN}✓ Ruff format: Code is properly formatted${NC}"
    else
        if [ -n "$FIX_MODE" ]; then
            echo -e "${YELLOW}→ Applying format fixes...${NC}"
            python -m ruff format app/ tests/
            echo -e "${GREEN}✓ Ruff format: Fixed${NC}"
        else
            echo -e "${YELLOW}! Ruff format: Code needs formatting (run with --fix)${NC}"
        fi
    fi
    
    # 3. Backend tests
    if [ "$SKIP_TESTS" = false ]; then
        echo -e "\n${YELLOW}→ Running backend tests...${NC}"
        if python -m pytest tests/ -q --tb=short; then
            echo -e "${GREEN}✓ Tests: All passed${NC}"
        else
            echo -e "${RED}✗ Tests: Some tests failed${NC}"
            FAILED=1
        fi
    else
        echo -e "\n${YELLOW}→ Skipping backend tests (--skip-tests)${NC}"
    fi
    
    cd ..
fi

# =============================================================================
# FRONTEND VALIDATION
# =============================================================================
if [ "$BACKEND_ONLY" = false ]; then
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  FRONTEND                                                         ${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        echo -e "${RED}✗ Frontend directory not found${NC}"
        exit 1
    fi
    
    cd frontend
    
    # Check node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}→ Installing dependencies...${NC}"
        npm install
    fi
    
    # 1. ESLint
    echo -e "\n${YELLOW}→ Running ESLint...${NC}"
    if [ -n "$FIX_MODE" ]; then
        if npx eslint src/ --fix --max-warnings 0; then
            echo -e "${GREEN}✓ ESLint: All checks passed${NC}"
        else
            echo -e "${RED}✗ ESLint: Linter errors found${NC}"
            FAILED=1
        fi
    else
        if npx eslint src/ --max-warnings 0; then
            echo -e "${GREEN}✓ ESLint: All checks passed${NC}"
        else
            echo -e "${RED}✗ ESLint: Linter errors found${NC}"
            FAILED=1
        fi
    fi
    
    # 2. TypeScript type-check
    echo -e "\n${YELLOW}→ Running TypeScript type-check...${NC}"
    if npx tsc --noEmit --skipLibCheck; then
        echo -e "${GREEN}✓ TypeScript: No type errors${NC}"
    else
        echo -e "${RED}✗ TypeScript: Type errors found${NC}"
        FAILED=1
    fi
    
    # 3. Build check
    if [ "$SKIP_BUILD" = false ]; then
        echo -e "\n${YELLOW}→ Building frontend...${NC}"
        if npm run build > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Build: Successful${NC}"
        else
            echo -e "${RED}✗ Build: Failed${NC}"
            FAILED=1
        fi
    else
        echo -e "\n${YELLOW}→ Skipping build check (--skip-build)${NC}"
    fi
    
    cd ..
fi

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  SUMMARY                                                          ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ ALL VALIDATIONS PASSED                                        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}\n"
    exit 0
else
    echo -e "\n${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ SOME VALIDATIONS FAILED                                       ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}\n"
    exit 1
fi
