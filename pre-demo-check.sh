#!/bin/bash

# Pre-Demo Verification Script
# Run this before your demo to ensure everything is ready

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                                  ║${NC}"
echo -e "${PURPLE}║           🎬 Pre-Demo Verification Script 🎬                     ║${NC}"
echo -e "${PURPLE}║                                                                  ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Function to check and report
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# Check 1: Docker
echo -e "${BLUE}━━━ Checking Prerequisites ━━━${NC}"
echo ""

if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
    if docker ps &> /dev/null; then
        check_pass "Docker is running"
    else
        check_fail "Docker is not running - please start Docker"
    fi
else
    check_fail "Docker is not installed"
fi

# Check 2: Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js is installed ($NODE_VERSION)"
else
    check_fail "Node.js is not installed"
fi

# Check 3: npm
if command -v npm &> /dev/null; then
    check_pass "npm is installed"
else
    check_fail "npm is not installed"
fi

# Check 4: Git
if command -v git &> /dev/null; then
    check_pass "Git is installed"
else
    check_fail "Git is not installed"
fi

echo ""

# Check 5: Repository
echo -e "${BLUE}━━━ Checking Repository ━━━${NC}"
echo ""

if [ -f "package.json" ]; then
    check_pass "In correct directory (package.json found)"
else
    check_fail "Not in correct directory - cd to datadog-demo-app"
fi

if [ -f "src/app.js" ]; then
    check_pass "Source files present"
else
    check_fail "Source files missing"
fi

if [ -f "Dockerfile" ]; then
    check_pass "Dockerfile present"
else
    check_fail "Dockerfile missing"
fi

if [ -f "build-with-git-metadata.sh" ]; then
    check_pass "Build script present"
    if [ -x "build-with-git-metadata.sh" ]; then
        check_pass "Build script is executable"
    else
        check_warn "Build script not executable - run: chmod +x build-with-git-metadata.sh"
    fi
else
    check_fail "Build script missing"
fi

echo ""

# Check 6: Git metadata
echo -e "${BLUE}━━━ Checking Git Configuration ━━━${NC}"
echo ""

GIT_URL=$(git config --get remote.origin.url 2>/dev/null || echo "")
if [ -n "$GIT_URL" ]; then
    check_pass "Git remote configured: $GIT_URL"
    if [[ "$GIT_URL" == *"eranrh86/datadog-demo-app"* ]]; then
        check_pass "Correct repository"
    else
        check_warn "Different repository: $GIT_URL"
    fi
else
    check_fail "Git remote not configured"
fi

COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
if [ -n "$COMMIT_SHA" ]; then
    check_pass "Current commit: ${COMMIT_SHA:0:7}"
else
    check_fail "Cannot get commit SHA"
fi

echo ""

# Check 7: Dependencies
echo -e "${BLUE}━━━ Checking Dependencies ━━━${NC}"
echo ""

if [ -d "node_modules" ]; then
    check_pass "Node modules installed"
else
    check_warn "Node modules not installed - run: npm install"
fi

if [ -f "node_modules/dd-trace/package.json" ]; then
    DD_TRACE_VERSION=$(node -p "require('./node_modules/dd-trace/package.json').version" 2>/dev/null || echo "unknown")
    check_pass "dd-trace installed (v$DD_TRACE_VERSION)"
else
    check_fail "dd-trace not installed - run: npm install"
fi

echo ""

# Check 8: Docker image
echo -e "${BLUE}━━━ Checking Docker Image ━━━${NC}"
echo ""

if docker images | grep -q "datadog-demo-app"; then
    IMAGE_ID=$(docker images datadog-demo-app:latest --format "{{.ID}}" | head -n1)
    check_pass "Docker image exists (${IMAGE_ID:0:12})"
else
    check_warn "Docker image not built - run: ./build-with-git-metadata.sh"
fi

echo ""

# Check 9: Environment variables
echo -e "${BLUE}━━━ Checking Environment Variables ━━━${NC}"
echo ""

if [ -n "$DD_API_KEY" ]; then
    check_pass "DD_API_KEY is set (${DD_API_KEY:0:10}...)"
else
    check_warn "DD_API_KEY not set - export DD_API_KEY=your_key"
fi

echo ""

# Check 10: Application status
echo -e "${BLUE}━━━ Checking Application Status ━━━${NC}"
echo ""

if docker ps | grep -q "datadog-demo-app"; then
    check_pass "Application is running"
    
    # Test health endpoint
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        check_pass "Application is responding"
        
        # Check if data is flowing
        RESPONSE=$(curl -s http://localhost:3000/api/health)
        if echo "$RESPONSE" | grep -q "healthy"; then
            check_pass "Application is healthy"
        else
            check_warn "Application may not be healthy"
        fi
    else
        check_warn "Application not responding on port 3000"
    fi
    
    # Check Git metadata in container
    GIT_REPO=$(docker exec datadog-demo-app env 2>/dev/null | grep DD_GIT_REPOSITORY_URL | cut -d'=' -f2 || echo "")
    GIT_SHA=$(docker exec datadog-demo-app env 2>/dev/null | grep DD_GIT_COMMIT_SHA | cut -d'=' -f2 || echo "")
    
    if [ -n "$GIT_REPO" ]; then
        check_pass "Git metadata configured in container"
        if [ -n "$GIT_SHA" ]; then
            check_pass "Commit SHA: ${GIT_SHA:0:7}"
        fi
    else
        check_warn "Git metadata not found in container - rebuild with ./build-with-git-metadata.sh"
    fi
else
    check_warn "Application is not running"
    echo ""
    echo "To start the application:"
    echo "  docker run -d --name datadog-demo-app -p 3000:3000 \\"
    echo "    -e DD_API_KEY=\$DD_API_KEY \\"
    echo "    -e DD_AGENT_HOST=host.docker.internal \\"
    echo "    datadog-demo-app:latest"
fi

echo ""

# Check 11: Demo scripts
echo -e "${BLUE}━━━ Checking Demo Scripts ━━━${NC}"
echo ""

for script in verify-datadog-features.sh demo-all-features.sh build-with-git-metadata.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            check_pass "$script is ready"
        else
            check_warn "$script not executable - run: chmod +x $script"
        fi
    else
        check_fail "$script missing"
    fi
done

echo ""

# Summary
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}Summary${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ Perfect! Everything is ready for your demo!${NC}"
    echo ""
    echo "You can now:"
    echo "  1. Open Datadog UI: https://app.datadoghq.com"
    echo "  2. Open DEMO_STEP_BY_STEP.md for the full guide"
    echo "  3. Print DEMO_CHEAT_SHEET_PRINTABLE.md"
    echo "  4. Start demoing!"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Ready with $WARNINGS warning(s)${NC}"
    echo ""
    echo "You can proceed, but consider addressing the warnings above."
else
    echo -e "${RED}✗ Found $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before starting your demo."
fi

echo ""

# Quick fix suggestions
if [ $ERRORS -gt 0 ] || [ $WARNINGS -gt 0 ]; then
    echo -e "${BLUE}Quick Fixes:${NC}"
    echo ""
    
    if [ ! -d "node_modules" ]; then
        echo "  npm install"
    fi
    
    if ! docker images | grep -q "datadog-demo-app"; then
        echo "  ./build-with-git-metadata.sh"
    fi
    
    if [ -z "$DD_API_KEY" ]; then
        echo "  export DD_API_KEY=your_datadog_api_key"
    fi
    
    if ! docker ps | grep -q "datadog-demo-app"; then
        echo "  docker run -d --name datadog-demo-app -p 3000:3000 \\"
        echo "    -e DD_API_KEY=\$DD_API_KEY \\"
        echo "    -e DD_AGENT_HOST=host.docker.internal \\"
        echo "    datadog-demo-app:latest"
    fi
    
    echo ""
fi

# Next steps
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "  1. Review: DEMO_STEP_BY_STEP.md"
echo "  2. Print: DEMO_CHEAT_SHEET_PRINTABLE.md"
echo "  3. Test: curl http://localhost:3000/api/health"
echo "  4. Demo: ./demo-all-features.sh"
echo ""

exit $ERRORS

