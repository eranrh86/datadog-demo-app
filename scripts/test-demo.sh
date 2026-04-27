#!/bin/bash

# Test script to generate demo data for Datadog
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get service URL
MINIKUBE_IP=$(minikube ip)
NODE_PORT=$(kubectl get svc datadog-demo-service -n datadog-demo -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "30080")
BASE_URL="http://${MINIKUBE_IP}:${NODE_PORT}"

echo -e "${BLUE}🧪 Running Datadog Demo Test Scenarios...${NC}"
echo -e "Base URL: ${GREEN}${BASE_URL}${NC}\n"

# Function to make HTTP request and show response
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}Testing: ${description}${NC}"
    echo -e "  ${method} ${endpoint}"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X ${method} -H "Content-Type: application/json" -d "$data" "${BASE_URL}${endpoint}" || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" -X ${method} "${BASE_URL}${endpoint}" || echo "000")
    fi
    
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "  ✅ ${GREEN}Success (${http_code})${NC}"
    elif [ "$http_code" -ge 400 ] && [ "$http_code" -lt 600 ]; then
        echo -e "  ⚠️  ${YELLOW}Expected Error (${http_code})${NC}"
    else
        echo -e "  ❌ ${RED}Failed (${http_code})${NC}"
    fi
    
    echo -e "  Response: $(echo "$body" | jq -c . 2>/dev/null || echo "$body" | head -c 100)...\n"
    sleep 1
}

# 1. Log Annotations Demo
echo -e "${BLUE}📊 1. Log Annotations & Volume Gauging${NC}"
make_request "GET" "/" "" "Homepage access (generates log volume metrics)"
make_request "GET" "/api/health" "" "Health check (system metrics)"
make_request "GET" "/api/health/metrics" "" "Custom metrics endpoint"

# 2. Normal API Usage (generates traces and logs)
echo -e "${BLUE}👥 2. Normal API Usage (Tracing & Logging)${NC}"
make_request "GET" "/api/users" "" "Get all users"
make_request "GET" "/api/users/1" "" "Get user by ID"
make_request "GET" "/api/orders" "" "Get all orders (with performance monitoring)"
make_request "GET" "/api/orders/1" "" "Get order by ID"

# 3. Create some data
echo -e "${BLUE}📝 3. Data Creation (Business Logic Tracing)${NC}"
make_request "POST" "/api/users" '{"name":"Demo User","email":"demo@example.com","role":"user"}' "Create new user"
make_request "POST" "/api/orders" '{"userId":1,"product":"Demo Product","amount":99.99}' "Create normal order"
make_request "POST" "/api/orders" '{"userId":1,"product":"Expensive Item","amount":1500.00}' "Create high-value order (triggers approval workflow)"

# 4. Code Insights Demo - Runtime Errors
echo -e "${BLUE}💥 4. Code Insights - Runtime Errors${NC}"
make_request "GET" "/api/users/999" "" "Trigger runtime error (user 999)"
make_request "GET" "/api/orders/666" "" "Trigger intentional error (order 666)"
make_request "GET" "/api/orders/500" "" "Trigger database error simulation"
make_request "GET" "/error/runtime" "" "Direct runtime error endpoint"

# 5. Security Vulnerabilities Demo
echo -e "${BLUE}🔒 5. Code Insights - Security Vulnerabilities${NC}"
make_request "GET" "/vulnerable/123" "" "SQL injection vulnerability demo"
make_request "GET" "/vulnerable/'; DROP TABLE users; --" "" "SQL injection attempt"

# 6. Performance Issues Demo
echo -e "${BLUE}⚡ 6. Performance Monitoring${NC}"
make_request "GET" "/memory-leak" "" "Memory leak simulation"
for i in {1..5}; do
    make_request "GET" "/api/orders" "" "Load test - request $i/5"
done

# 7. Cache behavior testing
echo -e "${BLUE}💾 7. Cache Behavior Testing${NC}"
for i in {1..3}; do
    make_request "GET" "/api/orders/user/1" "" "Cache test - request $i/3"
done

# 8. Generate some 404s and validation errors
echo -e "${BLUE}❌ 8. Error Scenarios${NC}"
make_request "GET" "/api/users/9999" "" "User not found (404)"
make_request "GET" "/api/orders/9999" "" "Order not found (404)"
make_request "POST" "/api/users" '{"name":"Invalid User"}' "Validation error (missing email)"
make_request "GET" "/nonexistent-endpoint" "" "Route not found (404)"

echo -e "${GREEN}✅ Demo test scenarios completed!${NC}"
echo -e "\n${YELLOW}📈 Check your Datadog dashboard for:${NC}"
echo -e "  • Log volume metrics and annotations"
echo -e "  • APM traces for all requests"
echo -e "  • Runtime errors and exceptions"
echo -e "  • Security vulnerability alerts"
echo -e "  • Performance metrics and slow queries"
echo -e "  • Custom business metrics"
echo -e "\n${BLUE}🔍 To run flaky tests:${NC}"
echo -e "  cd /path/to/datadog-demo-app && npm test"
