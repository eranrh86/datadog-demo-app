#!/bin/bash

# Comprehensive Demo Script for All 4 Datadog Features
# This script triggers all demo scenarios for Code Insights, View in IDE, Static Analysis, and Exception Replay

set -e

# Configuration
APP_URL="${APP_URL:-http://localhost:3000}"
DELAY=2

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                                  ║${NC}"
echo -e "${PURPLE}║       🐕 Datadog Demo App - All Features Demo Script 🐕         ║${NC}"
echo -e "${PURPLE}║                                                                  ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Repository: https://github.com/eranrh86/datadog-demo-app"
echo "Service: datadog-demo-app"
echo "App URL: $APP_URL"
echo ""
echo "This script will demonstrate all 4 key Datadog features:"
echo "  1. Code Insights (Runtime Errors & Vulnerabilities)"
echo "  2. View in IDE (Source Code Integration)"
echo "  3. Static Code Analysis (Pre-commit checks)"
echo "  4. Exception Replay (Production debugging)"
echo ""
read -p "Press Enter to start the demo..."
echo ""

# Function to make HTTP request and show result
make_request() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    echo -e "${BLUE}→${NC} $description"
    echo "  ${method} ${APP_URL}${endpoint}"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X ${method} "${APP_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1 || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" -X ${method} "${APP_URL}${endpoint}" 2>&1 || echo "000")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "  ${GREEN}✓ Status: ${http_code}${NC}"
    elif [ "$http_code" -ge 400 ]; then
        echo -e "  ${YELLOW}⚠ Status: ${http_code} (Expected for demo)${NC}"
    else
        echo -e "  ${RED}✗ Status: ${http_code}${NC}"
    fi
    
    echo ""
    sleep $DELAY
}

# ============================================================================
# Feature 1: Static Code Analysis
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1️⃣  Static Code Analysis Demo${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Running ESLint to detect security issues..."
echo ""

npm run lint 2>&1 | head -n 30 || true

echo ""
echo -e "${GREEN}✓ Static Analysis Complete${NC}"
echo ""
echo "Check Datadog for:"
echo "  • Code Insights → Vulnerabilities"
echo "  • Security issues: SQL injection, eval usage, object injection"
echo ""
read -p "Press Enter to continue to Code Insights demo..."
echo ""

# ============================================================================
# Feature 2: Code Insights - Runtime Errors
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2️⃣  Code Insights - Runtime Errors Demo${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

make_request "GET" "/api/users/999" "Triggering null pointer exception (user 999)"
make_request "GET" "/api/orders/666" "Triggering intentional error (order 666)"
make_request "GET" "/api/orders/500" "Triggering database connection error (order 500)"
make_request "GET" "/error/runtime" "Triggering direct runtime error"

echo -e "${GREEN}✓ Runtime Errors Generated${NC}"
echo ""
echo "Check Datadog for:"
echo "  • APM → Error Tracking → See runtime errors"
echo "  • Code Insights → Runtime Errors section"
echo "  • Error details with stack traces"
echo ""
read -p "Press Enter to continue to Security Vulnerabilities demo..."
echo ""

# ============================================================================
# Feature 2b: Code Insights - Security Vulnerabilities
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2️⃣b Code Insights - Security Vulnerabilities Demo${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

make_request "GET" "/vulnerable/123" "Accessing vulnerable endpoint (SQL injection)"
make_request "GET" "/vulnerable/'; DROP TABLE users; --" "SQL injection attempt"
make_request "POST" "/api/users" "Creating user without email validation" '{"name":"Hacker","email":"not-validated@evil.com"}'

echo -e "${GREEN}✓ Security Vulnerabilities Triggered${NC}"
echo ""
echo "Check Datadog for:"
echo "  • Code Insights → Vulnerabilities"
echo "  • SQL injection detection"
echo "  • Input validation issues"
echo ""
read -p "Press Enter to continue to View in IDE demo..."
echo ""

# ============================================================================
# Feature 3: View in IDE
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3️⃣  View in IDE Demo${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Generating errors with full source code context..."
echo ""

make_request "GET" "/api/users/999" "Error with source mapping (users.js:48)"
make_request "GET" "/error/runtime" "Error with source mapping (app.js:107)"
make_request "GET" "/api/orders/666" "Error with source mapping (orders.js:66)"

echo -e "${GREEN}✓ Errors with Source Code Context Generated${NC}"
echo ""
echo "Check Datadog for:"
echo "  • APM → Error Tracking → Click any error"
echo "  • Look for 'View in IDE' button"
echo "  • Click it to jump to exact line in source code"
echo "  • Repository: https://github.com/eranrh86/datadog-demo-app"
echo ""
echo "Files with errors:"
echo "  • src/routes/users.js:48 - Null pointer exception"
echo "  • src/app.js:107 - Runtime error"
echo "  • src/routes/orders.js:66 - Intentional error"
echo ""
read -p "Press Enter to continue to Exception Replay demo..."
echo ""

# ============================================================================
# Feature 4: Exception Replay
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}4️⃣  Exception Replay Demo${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Generating errors with full request/response context..."
echo ""

make_request "POST" "/api/orders" "Invalid order creation" '{"userId":"invalid","product":"Test","amount":"not-a-number"}'
make_request "GET" "/api/users/999" "User fetch error with context"
make_request "GET" "/api/health/ready" "Health check failure (random)"
make_request "GET" "/api/health/ready" "Health check failure (random)"
make_request "GET" "/api/health/ready" "Health check failure (random)"

echo -e "${GREEN}✓ Exception Replay Data Generated${NC}"
echo ""
echo "Check Datadog for:"
echo "  • APM → Error Tracking → Click any error"
echo "  • See full request details (headers, body, params)"
echo "  • See full response details"
echo "  • See environment state"
echo "  • See user session information"
echo "  • See complete stack trace"
echo ""
read -p "Press Enter to continue to Flaky Tests demo..."
echo ""

# ============================================================================
# Bonus: Flaky Tests
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}5️⃣  Bonus: Flaky Test Detection Demo${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Running tests multiple times to demonstrate flaky behavior..."
echo ""

for i in {1..3}; do
    echo "Test run #$i:"
    npm test 2>&1 | tail -n 5 || true
    echo ""
    sleep 1
done

echo -e "${GREEN}✓ Flaky Tests Executed${NC}"
echo ""
echo "Check Datadog for:"
echo "  • CI/CD → Test Visibility"
echo "  • Flaky Tests section"
echo "  • See tests that fail randomly"
echo ""

# ============================================================================
# Normal Operations (for comparison)
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}6️⃣  Normal Operations (for comparison)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Generating normal traffic for comparison..."
echo ""

make_request "GET" "/" "Homepage"
make_request "GET" "/api/health" "Health check"
make_request "GET" "/api/users" "Get all users"
make_request "GET" "/api/users/1" "Get user by ID"
make_request "GET" "/api/orders" "Get all orders"
make_request "GET" "/api/orders/1" "Get order by ID"
make_request "GET" "/api/health/metrics" "Get metrics"

echo -e "${GREEN}✓ Normal Operations Complete${NC}"
echo ""

# ============================================================================
# Summary
# ============================================================================
echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                                  ║${NC}"
echo -e "${PURPLE}║                     🎉 Demo Complete! 🎉                         ║${NC}"
echo -e "${PURPLE}║                                                                  ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ All 4 Datadog features demonstrated!${NC}"
echo ""
echo "What was triggered:"
echo ""
echo "1. ✓ Static Code Analysis"
echo "     • ESLint security checks"
echo "     • Detected SQL injection, eval, object injection"
echo ""
echo "2. ✓ Code Insights"
echo "     • 4 runtime errors generated"
echo "     • 3 security vulnerabilities triggered"
echo "     • Health check failures"
echo ""
echo "3. ✓ View in IDE"
echo "     • Errors with source code mapping"
echo "     • GitHub integration configured"
echo "     • Repository: https://github.com/eranrh86/datadog-demo-app"
echo ""
echo "4. ✓ Exception Replay"
echo "     • Full request/response context"
echo "     • Stack traces with environment state"
echo "     • Error correlation with logs"
echo ""
echo "5. ✓ Flaky Tests"
echo "     • Tests run multiple times"
echo "     • Random failures demonstrated"
echo ""
echo -e "${YELLOW}📊 View Results in Datadog:${NC}"
echo ""
echo "  • APM → Services → datadog-demo-app"
echo "  • Error Tracking → See all errors with 'View in IDE'"
echo "  • Code Insights → Runtime errors & vulnerabilities"
echo "  • CI/CD → Test Visibility → Flaky tests"
echo ""
echo -e "${BLUE}🔗 Links:${NC}"
echo "  • Datadog: https://app.datadoghq.com"
echo "  • GitHub: https://github.com/eranrh86/datadog-demo-app"
echo ""
echo -e "${GREEN}Happy demoing! 🐕${NC}"
echo ""

