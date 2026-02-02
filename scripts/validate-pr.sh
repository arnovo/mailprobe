#!/bin/bash
# Pre-PR validation: run before creating a Pull Request
# Usage: ./scripts/validate-pr.sh [base-branch]

set -e

BASE_BRANCH="${1:-main}"
CURRENT_BRANCH=$(git branch --show-current)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Pre-Pull Request Validation        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Current branch: ${YELLOW}$CURRENT_BRANCH${NC}"
echo -e "Base: ${YELLOW}$BASE_BRANCH${NC}"
echo ""

ERRORS=0

# ============================================
# 1. Verify we're not on main
# ============================================
echo -e "${YELLOW}▶ Checking branch...${NC}"
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo -e "${RED}✗ Cannot create PR from main/master${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ Branch OK: $CURRENT_BRANCH${NC}"
fi

# ============================================
# 2. Verify pending commits
# ============================================
echo -e "${YELLOW}▶ Checking commits...${NC}"
COMMITS=$(git log --oneline "$BASE_BRANCH..HEAD" 2>/dev/null | wc -l | tr -d ' ')
if [ "$COMMITS" -eq 0 ]; then
    echo -e "${RED}✗ No new commits relative to $BASE_BRANCH${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ $COMMITS commit(s) to include in PR${NC}"
    git log --oneline "$BASE_BRANCH..HEAD" | head -10
fi

# ============================================
# 3. Verify commit format (Conventional Commits)
# ============================================
echo ""
echo -e "${YELLOW}▶ Checking commit format...${NC}"
INVALID_COMMITS=0
while IFS= read -r commit; do
    if [ -n "$commit" ]; then
        # Verify it starts with valid type
        if ! echo "$commit" | grep -qE "^[a-f0-9]+ (feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?(!)?:"; then
            echo -e "${RED}  ✗ $commit${NC}"
            INVALID_COMMITS=$((INVALID_COMMITS + 1))
        fi
    fi
done <<< "$(git log --oneline "$BASE_BRANCH..HEAD" 2>/dev/null)"

if [ "$INVALID_COMMITS" -gt 0 ]; then
    echo -e "${RED}✗ $INVALID_COMMITS commit(s) don't follow Conventional Commits${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ All commits follow Conventional Commits${NC}"
fi

# ============================================
# 4. Verify backend tests
# ============================================
echo ""
echo -e "${YELLOW}▶ Running backend tests...${NC}"
cd backend
PYTHON_CMD="python3"
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
fi

if $PYTHON_CMD -m pytest tests/ -q --tb=short 2>&1 | tail -5; then
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}✓ Backend tests OK${NC}"
    else
        echo -e "${RED}✗ Backend tests failed${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗ Error running tests${NC}"
    ERRORS=$((ERRORS + 1))
fi
cd ..

# ============================================
# 5. Verify backend linting
# ============================================
echo ""
echo -e "${YELLOW}▶ Checking backend linting...${NC}"
cd backend
if $PYTHON_CMD -m ruff check app/ --quiet; then
    echo -e "${GREEN}✓ Ruff OK${NC}"
else
    echo -e "${RED}✗ Ruff found errors${NC}"
    ERRORS=$((ERRORS + 1))
fi
cd ..

# ============================================
# 6. Verify TypeScript frontend
# ============================================
echo ""
echo -e "${YELLOW}▶ Checking TypeScript frontend...${NC}"
cd frontend
if npx tsc --noEmit --skipLibCheck 2>/dev/null; then
    echo -e "${GREEN}✓ TypeScript OK${NC}"
else
    echo -e "${RED}✗ TypeScript errors${NC}"
    ERRORS=$((ERRORS + 1))
fi
cd ..

# ============================================
# 7. Verify no secrets
# ============================================
echo ""
echo -e "${YELLOW}▶ Checking for secrets...${NC}"
SECRETS_PATTERN='(api_key|apikey|password|secret|token|private_key)[[:space:]]*[=:][[:space:]]*["\x27][^"\x27]{8,}'
if git diff "$BASE_BRANCH..HEAD" | grep -iE "$SECRETS_PATTERN" > /dev/null 2>&1; then
    echo -e "${RED}✗ Possible secrets detected in changes${NC}"
    echo -e "${YELLOW}  Check: git diff $BASE_BRANCH..HEAD${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ No secrets detected${NC}"
fi

# ============================================
# Summary
# ============================================
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}✗ Validation failed: $ERRORS error(s)${NC}"
    echo -e "${YELLOW}Fix the errors before creating the PR${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Validation successful - ready to create PR${NC}"
    echo ""
    echo -e "Suggested command:"
    echo -e "${YELLOW}gh pr create --title \"...\" --body \"...\"${NC}"
    exit 0
fi
