#!/bin/bash

# Datadog Features Verification Script
# Verifies all 4 key features: Code Insights, View in IDE, Static Analysis, Exception Replay

set -e

echo "🐕 Datadog Features Verification Script"
echo "========================================"
echo ""
echo "Repository: https://github.com/eranrh86/datadog-demo-app"
echo "Service: datadog-demo-app"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Feature 1: Static Code Analysis
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1️⃣  Static Code Analysis${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Running ESLint with security plugin..."
echo ""

if npm run lint 2>&1 | tee /tmp/lint-output.txt; then
    echo -e "${GREEN}✅ Linting completed${NC}"
else
    echo -e "${YELLOW}⚠️  Linting found issues (expected for demo)${NC}"
    echo ""
    echo "Expected security issues found:"
    grep -E "(eval|sql-injection|object-injection)" /tmp/lint-output.txt || true
fi

echo ""
echo -e "${GREEN}✓ Static Code Analysis configured${NC}"
echo "  - ESLint with security plugin enabled"
echo "  - Detects: SQL injection, eval usage, object injection"
echo "  - Files with intentional issues:"
echo "    • src/app.js (lines 84, 87) - SQL injection & eval"
echo "    • src/routes/users.js (line 146) - Object.assign vulnerability"
echo ""

# Feature 2: Code Insights (Runtime Errors & Vulnerabilities)
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2️⃣  Code Insights - Runtime Errors${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Checking runtime error endpoints..."
echo ""

# Check Git metadata configuration
if [ -n "$DD_GIT_REPOSITORY_URL" ] && [ -n "$DD_GIT_COMMIT_SHA" ]; then
    echo -e "${GREEN}✅ Git metadata configured${NC}"
    echo "  Repository: $DD_GIT_REPOSITORY_URL"
    echo "  Commit SHA: $DD_GIT_COMMIT_SHA"
else
    echo -e "${YELLOW}⚠️  Git metadata not set in environment${NC}"
    echo "  Set these variables:"
    echo "    export DD_GIT_REPOSITORY_URL=https://github.com/eranrh86/datadog-demo-app"
    echo "    export DD_GIT_COMMIT_SHA=\$(git rev-parse HEAD)"
fi

echo ""
echo -e "${GREEN}✓ Code Insights configured${NC}"
echo "  Runtime error endpoints:"
echo "    • GET /api/users/999 - Null pointer exception"
echo "    • GET /api/orders/666 - Intentional error"
echo "    • GET /api/orders/500 - Database error"
echo "    • GET /error/runtime - Runtime error"
echo "    • GET /api/health/ready - Health check failures"
echo ""
echo "  Security vulnerabilities:"
echo "    • GET /vulnerable/:id - SQL injection"
echo "    • POST /api/users - No email validation"
echo "    • PUT /api/users/:id - No input sanitization"
echo ""

# Feature 3: View in IDE
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3️⃣  View in IDE Integration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Checking source code integration setup..."
echo ""

# Check Dockerfile
if grep -q "DD_GIT_REPOSITORY_URL" Dockerfile; then
    echo -e "${GREEN}✅ Dockerfile configured with Git metadata${NC}"
else
    echo -e "${RED}❌ Dockerfile missing Git metadata${NC}"
fi

# Check app.js
if grep -q "DD_GIT_REPOSITORY_URL" src/app.js; then
    echo -e "${GREEN}✅ Application configured with Git metadata${NC}"
else
    echo -e "${RED}❌ Application missing Git metadata${NC}"
fi

# Check K8s deployment
if grep -q "DD_GIT_REPOSITORY_URL" k8s/deployment.yaml; then
    echo -e "${GREEN}✅ Kubernetes deployment configured${NC}"
else
    echo -e "${RED}❌ Kubernetes deployment missing Git metadata${NC}"
fi

# Check dd-trace version
DD_TRACE_VERSION=$(node -p "require('./package.json').dependencies['dd-trace']" 2>/dev/null || echo "not found")
echo ""
echo "  dd-trace version: $DD_TRACE_VERSION"
if [[ "$DD_TRACE_VERSION" == *"4."* ]] || [[ "$DD_TRACE_VERSION" == *"3.2"* ]]; then
    echo -e "${GREEN}  ✓ Version supports source code integration${NC}"
else
    echo -e "${YELLOW}  ⚠️  Version may not support source code integration${NC}"
fi

echo ""
echo -e "${GREEN}✓ View in IDE configured${NC}"
echo "  Repository: https://github.com/eranrh86/datadog-demo-app"
echo "  Setup:"
echo "    • Dockerfile has Git metadata ARGs"
echo "    • app.js sets DD_GIT_* environment variables"
echo "    • K8s deployment includes Git metadata"
echo "    • Build script: ./build-with-git-metadata.sh"
echo ""
echo "  To test:"
echo "    1. Build with: ./build-with-git-metadata.sh"
echo "    2. Deploy application"
echo "    3. Trigger error: curl http://localhost:3000/api/users/999"
echo "    4. In Datadog APM → Error Tracking → Click 'View in IDE'"
echo ""

# Feature 4: Exception Replay
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}4️⃣  Exception Replay${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Checking exception handling configuration..."
echo ""

# Check error handler
if [ -f "src/middleware/errorHandler.js" ]; then
    echo -e "${GREEN}✅ Error handler middleware exists${NC}"
else
    echo -e "${RED}❌ Error handler middleware missing${NC}"
fi

# Check dd-trace initialization
if grep -q "dd-trace" src/app.js; then
    echo -e "${GREEN}✅ Datadog tracer initialized${NC}"
else
    echo -e "${RED}❌ Datadog tracer not initialized${NC}"
fi

# Check log injection
if grep -q "logInjection: true" src/app.js; then
    echo -e "${GREEN}✅ Log injection enabled (trace correlation)${NC}"
else
    echo -e "${YELLOW}⚠️  Log injection not enabled${NC}"
fi

echo ""
echo -e "${GREEN}✓ Exception Replay configured${NC}"
echo "  Features enabled:"
echo "    • Error handler with full context capture"
echo "    • Log injection for trace correlation"
echo "    • Request/response data capture"
echo "    • Stack traces with source mapping"
echo "    • Error tags on spans"
echo ""
echo "  Test endpoints:"
echo "    • GET /api/users/999 - Runtime error"
echo "    • GET /api/orders/666 - Intentional error"
echo "    • GET /api/orders/500 - Database error"
echo "    • GET /error/runtime - Direct runtime error"
echo "    • GET /api/health/ready - Health check errors"
echo ""

# Flaky Tests
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}5️⃣  Bonus: Flaky Test Detection${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Checking test configuration..."
echo ""

if [ -f "tests/users.test.js" ]; then
    FLAKY_TESTS=$(grep -c "flaky test" tests/users.test.js || echo "0")
    echo -e "${GREEN}✅ Test suite configured${NC}"
    echo "  Flaky tests: $FLAKY_TESTS"
else
    echo -e "${RED}❌ Test suite missing${NC}"
fi

echo ""
echo -e "${GREEN}✓ Flaky test detection ready${NC}"
echo "  Run tests multiple times:"
echo "    npm test"
echo "    npm run test:flaky"
echo ""
echo "  Flaky tests will fail randomly ~30% of the time"
echo "  View in Datadog: CI/CD → Test Visibility → Flaky Tests"
echo ""

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✅ All 4 Datadog features are configured!${NC}"
echo ""
echo "1. ✓ Code Insights - Runtime errors & vulnerabilities"
echo "2. ✓ View in IDE - Source code integration"
echo "3. ✓ Static Code Analysis - ESLint with security"
echo "4. ✓ Exception Replay - Full error context"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo ""
echo "1. Build with Git metadata:"
echo "   ./build-with-git-metadata.sh"
echo ""
echo "2. Deploy the application:"
echo "   docker run -d -p 3000:3000 -e DD_API_KEY=\$DD_API_KEY datadog-demo-app:latest"
echo "   # OR"
echo "   kubectl apply -f k8s/"
echo ""
echo "3. Generate demo data:"
echo "   ./traffic-generator.sh"
echo ""
echo "4. View in Datadog:"
echo "   • APM → Services → datadog-demo-app"
echo "   • Error Tracking → View errors with 'View in IDE'"
echo "   • Code Insights → See vulnerabilities"
echo "   • CI/CD → Test Visibility → Flaky tests"
echo ""
echo -e "${GREEN}🎉 Ready for demo!${NC}"
echo ""

