#!/bin/bash
# Pre-commit hook for Email Finder MVP
# Runs linters, type-check, secret detection and tests

set -e

echo "🔍 Running pre-commit hooks..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
BACKEND_CHANGED=$(echo "$STAGED_FILES" | grep "^backend/" || true)
FRONTEND_CHANGED=$(echo "$STAGED_FILES" | grep -E "^frontend/src/.*\.(ts|tsx|js|jsx)$" || true)

# Python code from backend (app/, not tests/) - requires adding tests
BACKEND_CODE_PY=$(echo "$STAGED_FILES" | grep -E "^backend/app/.*\.py$" || true)

# ============================================
# 1. Secret detection
# ============================================
echo -e "${YELLOW}▶ Checking for secrets...${NC}"
SECRETS_PATTERN='(api_key|apikey|api-key|password|passwd|secret|token|private_key|privatekey|credential|auth_token|access_token|refresh_token)[[:space:]]*[=:][[:space:]]*["\x27][^"\x27]{8,}'

if git diff --cached --diff-filter=ACM -U0 | grep -iE "$SECRETS_PATTERN" > /dev/null 2>&1; then
    echo -e "${RED}✗ Possible secret detected in code${NC}"
    echo -e "${RED}  Check the lines with: git diff --cached${NC}"
    echo -e "${YELLOW}  If false positive, use: git commit --no-verify${NC}"
    exit 1
fi
echo -e "${GREEN}✓ No secrets detected${NC}"

# ============================================
# 2. Check file size (max 500KB)
# ============================================
MAX_FILE_SIZE=512000  # 500KB in bytes
echo -e "${YELLOW}▶ Checking file sizes...${NC}"

for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        FILE_SIZE=$(wc -c < "$file" 2>/dev/null || echo 0)
        if [ "$FILE_SIZE" -gt "$MAX_FILE_SIZE" ]; then
            echo -e "${RED}✗ File too large: $file ($(($FILE_SIZE / 1024))KB > 500KB)${NC}"
            exit 1
        fi
    fi
done
echo -e "${GREEN}✓ File sizes OK${NC}"

# ============================================
# 3. Backend linter (ruff) - staged files only
# ============================================
if [ -n "$BACKEND_CHANGED" ]; then
    echo -e "${YELLOW}▶ Running ruff (backend)...${NC}"
    cd backend
    
    # Extract only staged .py files
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
            echo -e "${RED}✗ ruff found errors${NC}"
            cd ..
            exit 1
        fi
    fi
    cd ..
fi

# ============================================
# 4. Frontend linter (eslint) - staged files only
# ============================================
if [ -n "$FRONTEND_CHANGED" ]; then
    echo -e "${YELLOW}▶ Running eslint (frontend)...${NC}"
    cd frontend
    
    # Extract paths relative to frontend
    FRONTEND_FILES=$(echo "$FRONTEND_CHANGED" | sed 's|^frontend/||')
    
    if echo "$FRONTEND_FILES" | xargs npx eslint --max-warnings 0; then
        echo -e "${GREEN}✓ eslint OK${NC}"
    else
        echo -e "${RED}✗ eslint found errors${NC}"
        cd ..
        exit 1
    fi
    cd ..
fi

# ============================================
# 5. TypeScript type-check (frontend)
# ============================================
if [ -n "$FRONTEND_CHANGED" ]; then
    echo -e "${YELLOW}▶ Checking TypeScript types...${NC}"
    cd frontend
    
    if npx tsc --noEmit --skipLibCheck 2>&1 | head -20; then
        # tsc returns 0 if no errors
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo -e "${GREEN}✓ TypeScript OK${NC}"
        else
            echo -e "${RED}✗ TypeScript errors${NC}"
            cd ..
            exit 1
        fi
    fi
    cd ..
fi

# ============================================
# 5b. Frontend unit tests (Vitest)
# ============================================
if [ -n "$FRONTEND_CHANGED" ]; then
    echo -e "${YELLOW}▶ Running unit tests (frontend)...${NC}"
    cd frontend
    if npm run test; then
        echo -e "${GREEN}✓ frontend tests OK${NC}"
    else
        echo -e "${RED}✗ frontend tests failed${NC}"
        cd ..
        exit 1
    fi
    cd ..
fi

# ============================================
# 6. Backend tests (pytest)
# ============================================
if [ -n "$BACKEND_CHANGED" ]; then
    echo -e "${YELLOW}▶ Running tests (backend)...${NC}"
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
            echo -e "${RED}✗ tests failed${NC}"
            cd ..
            exit 1
        fi
    fi
    cd ..
fi

# ============================================
# 7. Verify new tests were added
# ============================================
# Only applies if there are changes in Python code in backend/app/ (not tests, not configs)
if [ -n "$BACKEND_CODE_PY" ] && [ -z "$SKIP_TEST_COUNT" ]; then
    echo -e "${YELLOW}▶ Checking test count...${NC}"
    cd backend
    
    # Use venv python if available
    PYTHON_CMD="python3"
    if [ -f ".venv/bin/python" ]; then
        PYTHON_CMD=".venv/bin/python"
    fi
    
    # Count tests in current state (staged)
    TESTS_STAGED=$($PYTHON_CMD -m pytest tests/ --collect-only -q 2>/dev/null | grep -c "test_" || echo 0)
    
    # Detect new test files (added, not in HEAD)
    cd ..
    NEW_TEST_FILES=$(git diff --cached --name-only --diff-filter=A | grep "^backend/tests/test_.*\.py$" || true)
    cd backend
    
    if [ -n "$NEW_TEST_FILES" ]; then
        # There are new test files, count how many tests they add
        NEW_TESTS=0
        for f in $NEW_TEST_FILES; do
            # Extract path relative to backend/
            REL_PATH=$(echo "$f" | sed 's|^backend/||')
            COUNT=$($PYTHON_CMD -m pytest "$REL_PATH" --collect-only -q 2>/dev/null | grep -c "test_" || echo 0)
            NEW_TESTS=$((NEW_TESTS + COUNT))
        done
        if [ "$NEW_TESTS" -gt 0 ]; then
            echo -e "${GREEN}✓ +$NEW_TESTS new tests in new files${NC}"
            cd ..
        else
            echo -e "${RED}✗ New test files but no valid tests${NC}"
            cd ..
            exit 1
        fi
    else
        # No new files, compare with HEAD
        git stash push --keep-index --quiet 2>/dev/null || true
        
        cd ..
        git checkout HEAD -- backend/tests/ 2>/dev/null || true
        cd backend
        TESTS_HEAD=$($PYTHON_CMD -m pytest tests/ --collect-only -q 2>/dev/null | grep -c "test_" || echo 0)
        
        cd ..
        git checkout --quiet -- backend/tests/ 2>/dev/null || true
        git stash pop --quiet 2>/dev/null || true
        
        if [ "$TESTS_STAGED" -le "$TESTS_HEAD" ]; then
            echo -e "${RED}✗ No new tests added ($TESTS_HEAD → $TESTS_STAGED)${NC}"
            echo -e "${YELLOW}  To force: SKIP_TEST_COUNT=1 git commit ...${NC}"
            echo -e "${YELLOW}  Or use: git commit --no-verify${NC}"
            exit 1
        else
            DIFF=$((TESTS_STAGED - TESTS_HEAD))
            echo -e "${GREEN}✓ +$DIFF new tests ($TESTS_HEAD → $TESTS_STAGED)${NC}"
        fi
    fi
fi

echo -e "${GREEN}✅ Pre-commit completed${NC}"
