#!/bin/bash

# Datadog Demo App with Datadog Integration
echo "🚀 Starting Datadog Demo App with Datadog Integration..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if DD_API_KEY is set
if [ -z "$DD_API_KEY" ]; then
    echo -e "${RED}❌ DD_API_KEY environment variable is not set${NC}"
    echo -e "${YELLOW}Please set your Datadog API key:${NC}"
    echo -e "export DD_API_KEY='your-datadog-api-key-here'"
    echo -e "${YELLOW}Or run with:${NC}"
    echo -e "DD_API_KEY='your-key' ./start-with-datadog.sh"
    echo ""
    echo -e "${YELLOW}For demo purposes, starting without Datadog integration...${NC}"
fi

# Navigate to project directory
cd "$(dirname "$0")"

# Kill any existing processes
echo "Cleaning up any existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start the application with environment variables
echo "Starting the application..."
NODE_ENV=development \
DD_SERVICE=datadog-demo-app \
DD_ENV=demo \
DD_VERSION=1.0.0 \
node src/app.js &

APP_PID=$!

# Wait for app to start
echo "Waiting for app to start..."
sleep 3

# Test the application
echo "Testing the application..."
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo -e "${GREEN}✅ Application is running on http://localhost:3000${NC}"
else
    echo -e "${RED}❌ Application failed to start${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎯 Demo app is ready!${NC}"
echo -e "${YELLOW}📊 Demo endpoints:${NC}"
echo -e "   • http://localhost:3000/ - Homepage"
echo -e "   • http://localhost:3000/api/users - Users API"
echo -e "   • http://localhost:3000/api/orders - Orders API"
echo -e "   • http://localhost:3000/api/health - Health check"
echo ""

if [ -n "$DD_API_KEY" ]; then
    echo -e "${GREEN}✅ Logs are being sent to Datadog${NC}"
    echo -e "${YELLOW}🔍 Check your Datadog Log Explorer for logs from service: datadog-demo-app${NC}"
else
    echo -e "${YELLOW}⚠️ Logs are only going to local files (logs/combined.log)${NC}"
    echo -e "${YELLOW}💡 Set DD_API_KEY to send logs to Datadog${NC}"
fi

echo ""
echo -e "To stop the app: kill $APP_PID"
echo -e "Or run: lsof -ti:3000 | xargs kill -9"
