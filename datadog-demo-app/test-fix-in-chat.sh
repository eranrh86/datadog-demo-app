#!/bin/bash

# Fix in Chat Testing Script
# Tests all scenarios for Fix in Chat demo

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
echo -e "${PURPLE}║              🤖 Fix in Chat - Test Script 🤖                     ║${NC}"
echo -e "${PURPLE}║                                                                  ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

APP_URL="${APP_URL:-http://localhost:3000}"

echo "Testing Fix in Chat scenarios..."
echo "App URL: $APP_URL"
echo ""

# Test 1: Verify Cursor Configuration
echo -e "${BLUE}━━━ Test 1: Cursor Configuration ━━━${NC}"
echo ""

if [ -f ".cursor/settings.json" ]; then
    echo -e "${GREEN}✓${NC} Cursor settings file exists"
    
    if grep -q "fixInChat" .cursor/settings.json; then
        echo -e "${GREEN}✓${NC} Fix in Chat is enabled"
    else
        echo -e "${YELLOW}⚠${NC} Fix in Chat not found in settings"
    fi
    
    if grep -q "datadog-demo-app" .cursor/settings.json; then
        echo -e "${GREEN}✓${NC} Service name configured"
    else
        echo -e "${RED}✗${NC} Service name not configured"
    fi
else
    echo -e "${RED}✗${NC} Cursor settings file missing"
fi

echo ""

# Test 2: Verify Datadog Configuration
echo -e "${BLUE}━━━ Test 2: Datadog Configuration ━━━${NC}"
echo ""

if [ -f ".datadog/config.json" ]; then
    echo -e "${GREEN}✓${NC} Datadog config file exists"
    
    if grep -q "datadog-demo-app" .datadog/config.json; then
        echo -e "${GREEN}✓${NC} Service configured in Datadog"
    fi
else
    echo -e "${YELLOW}⚠${NC} Datadog config file missing"
fi

echo ""

# Test 3: Trigger Runtime Errors
echo -e "${BLUE}━━━ Test 3: Runtime Errors (for Fix in Chat) ━━━${NC}"
echo ""

echo "Triggering errors that Fix in Chat can help with..."
echo ""

# Null pointer exception
echo -e "${BLUE}→${NC} Testing null pointer exception..."
RESPONSE=$(curl -s -w "\n%{http_code}" "$APP_URL/api/users/999" 2>&1 || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "500" ]; then
    echo -e "${GREEN}✓${NC} Null pointer error triggered (user 999)"
    echo "   File: src/routes/users.js:48"
    echo "   Fix: Replace null access with proper error handling"
else
    echo -e "${YELLOW}⚠${NC} Unexpected status: $HTTP_CODE"
fi

echo ""

# Intentional error
echo -e "${BLUE}→${NC} Testing intentional error..."
RESPONSE=$(curl -s -w "\n%{http_code}" "$APP_URL/api/orders/666" 2>&1 || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "500" ]; then
    echo -e "${GREEN}✓${NC} Intentional error triggered (order 666)"
    echo "   File: src/routes/orders.js:66"
    echo "   Fix: Remove throw statement or add proper error handling"
else
    echo -e "${YELLOW}⚠${NC} Unexpected status: $HTTP_CODE"
fi

echo ""

# Runtime error
echo -e "${BLUE}→${NC} Testing runtime error..."
RESPONSE=$(curl -s -w "\n%{http_code}" "$APP_URL/error/runtime" 2>&1 || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "500" ]; then
    echo -e "${GREEN}✓${NC} Runtime error triggered"
    echo "   File: src/app.js:107"
    echo "   Fix: Add null check before accessing properties"
else
    echo -e "${YELLOW}⚠${NC} Unexpected status: $HTTP_CODE"
fi

echo ""

# Test 4: Check Linter Errors
echo -e "${BLUE}━━━ Test 4: Linter Errors (for Fix in Chat) ━━━${NC}"
echo ""

echo "Running ESLint to find issues Fix in Chat can help with..."
echo ""

LINT_OUTPUT=$(npm run lint 2>&1 || true)

if echo "$LINT_OUTPUT" | grep -q "eval"; then
    echo -e "${GREEN}✓${NC} Eval vulnerability detected"
    echo "   File: src/app.js:91"
    echo "   Fix: Replace eval with template literals"
fi

if echo "$LINT_OUTPUT" | grep -q "object-injection"; then
    echo -e "${GREEN}✓${NC} Object injection detected"
    echo "   File: src/routes/users.js:146"
    echo "   Fix: Whitelist allowed fields before Object.assign"
fi

if echo "$LINT_OUTPUT" | grep -q "error"; then
    echo ""
    echo -e "${GREEN}✓${NC} Linter found issues that Fix in Chat can help resolve"
else
    echo -e "${YELLOW}⚠${NC} No linter errors found"
fi

echo ""

# Test 5: Check Flaky Tests
echo -e "${BLUE}━━━ Test 5: Flaky Tests (for Fix in Chat) ━━━${NC}"
echo ""

echo "Running tests to identify flaky tests..."
echo ""

PASS_COUNT=0
FAIL_COUNT=0

for i in {1..3}; do
    if npm test > /dev/null 2>&1; then
        ((PASS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
done

if [ $FAIL_COUNT -gt 0 ] && [ $PASS_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Flaky tests detected (passed $PASS_COUNT, failed $FAIL_COUNT)"
    echo "   File: tests/users.test.js:67"
    echo "   Fix: Remove timing dependency from test"
elif [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${YELLOW}⚠${NC} All tests passed (flaky tests may not have failed this time)"
else
    echo -e "${YELLOW}⚠${NC} All tests failed (may indicate a real issue)"
fi

echo ""

# Test 6: Verify Error Context
echo -e "${BLUE}━━━ Test 6: Error Context for AI ━━━${NC}"
echo ""

echo "Checking if errors have rich context for AI analysis..."
echo ""

# Check error handler
if grep -q "stack" src/middleware/errorHandler.js; then
    echo -e "${GREEN}✓${NC} Error handler captures stack traces"
fi

if grep -q "request" src/middleware/errorHandler.js; then
    echo -e "${GREEN}✓${NC} Error handler captures request context"
fi

# Check tracer
if grep -q "dd-trace" src/app.js; then
    echo -e "${GREEN}✓${NC} Datadog tracer initialized"
fi

if grep -q "logInjection: true" src/app.js; then
    echo -e "${GREEN}✓${NC} Log injection enabled (trace correlation)"
fi

echo ""

# Summary
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}Summary - Fix in Chat Test Results${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${GREEN}✅ Fix in Chat is ready to demo!${NC}"
echo ""

echo "Scenarios available for Fix in Chat:"
echo ""
echo "1. ${BLUE}Runtime Errors:${NC}"
echo "   • Null pointer exception (src/routes/users.js:48)"
echo "   • Intentional error (src/routes/orders.js:66)"
echo "   • Runtime error (src/app.js:107)"
echo ""
echo "2. ${BLUE}Security Vulnerabilities:${NC}"
echo "   • Eval usage (src/app.js:91)"
echo "   • Object injection (src/routes/users.js:146)"
echo "   • SQL injection (src/app.js:84)"
echo ""
echo "3. ${BLUE}Flaky Tests:${NC}"
echo "   • Timing-dependent test (tests/users.test.js:67)"
echo "   • Random failure test (tests/users.test.js:50)"
echo ""

echo -e "${YELLOW}📝 How to Demo Fix in Chat:${NC}"
echo ""
echo "Method 1: From Datadog"
echo "  1. Go to Datadog → APM → Error Tracking"
echo "  2. Click on any error"
echo "  3. Click 'Fix in Chat' button"
echo "  4. Cursor opens with AI suggestions"
echo ""
echo "Method 2: From Cursor"
echo "  1. Open file with error (e.g., src/routes/users.js)"
echo "  2. Select error line (line 48)"
echo "  3. Press Cmd+K (or Ctrl+K)"
echo "  4. Type: 'Fix this error using Datadog context'"
echo "  5. AI provides fix with explanation"
echo ""
echo "Method 3: From Linter"
echo "  1. Run: npm run lint"
echo "  2. Open file with error in Cursor"
echo "  3. Click on error or select line"
echo "  4. Press Cmd+K: 'Fix this security vulnerability'"
echo "  5. AI suggests secure alternative"
echo ""

echo -e "${BLUE}🔗 Documentation:${NC}"
echo "  • docs/FIX_IN_CHAT_GUIDE.md - Complete guide"
echo "  • DEMO_STEP_BY_STEP.md - Demo script"
echo ""

echo -e "${GREEN}Ready to demonstrate Fix in Chat! 🤖${NC}"
echo ""

