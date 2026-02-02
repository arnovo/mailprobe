#!/bin/bash
# Pre-push hook: lightweight validation before push
# For full PR validation, use: ./scripts/validate-pr.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Running pre-push hooks..."

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# ============================================
# 1. Verify not pushing directly to main
# ============================================
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    # Allow push to main only if merge/fast-forward
    # Block direct commits
    LOCAL_COMMITS=$(git log origin/main..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')
    if [ "$LOCAL_COMMITS" -gt 0 ]; then
        echo -e "${YELLOW}⚠ Push to main with $LOCAL_COMMITS local commit(s)${NC}"
        echo -e "${YELLOW}  Consider using a branch and PR${NC}"
        # Don't block, just warn
    fi
fi

# ============================================
# 2. Verify recent commits format
# ============================================
echo -e "${YELLOW}▶ Checking commits...${NC}"
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
    echo -e "${RED}✗ $INVALID commit(s) don't follow Conventional Commits${NC}"
    echo -e "${YELLOW}  To force: git push --no-verify${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Pre-push OK${NC}"
