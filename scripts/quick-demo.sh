#!/bin/bash

# Quick Demo Setup Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Datadog Demo Quick Setup${NC}"
echo -e "${YELLOW}This script will set up everything for your Datadog demo${NC}\n"

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check if minikube is available
if ! command -v minikube &> /dev/null; then
    echo -e "${RED}❌ Minikube not found. Please install minikube first.${NC}"
    exit 1
fi

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 16+ first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites found${NC}\n"

# Navigate to project directory
cd "$(dirname "$0")/.."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
    npm install
fi

# Create logs directory
mkdir -p logs

# Deploy to minikube
echo -e "${BLUE}🚀 Deploying to minikube...${NC}"
./scripts/deploy.sh

# Wait a moment for deployment to stabilize
echo -e "${BLUE}⏳ Waiting for deployment to stabilize...${NC}"
sleep 10

# Generate initial demo data
echo -e "${BLUE}📊 Generating demo data...${NC}"
./scripts/test-demo.sh

# Run flaky tests to demonstrate test insights
echo -e "${BLUE}🧪 Running flaky tests (for demo purposes)...${NC}"
npm test || true  # Don't fail if tests fail (they're supposed to be flaky)

# Show security issues
echo -e "${BLUE}🔒 Running security analysis...${NC}"
npm run lint || true  # Don't fail on linting errors (they're intentional)

# Get application URL
MINIKUBE_IP=$(minikube ip)
NODE_PORT=$(kubectl get svc datadog-demo-service -n datadog-demo -o jsonpath='{.spec.ports[0].nodePort}')
APP_URL="http://${MINIKUBE_IP}:${NODE_PORT}"

echo -e "\n${GREEN}🎉 Demo setup complete!${NC}"
echo -e "\n${YELLOW}📋 Demo Checklist:${NC}"
echo -e "  ✅ Application deployed to minikube"
echo -e "  ✅ Demo data generated"
echo -e "  ✅ Flaky tests executed"
echo -e "  ✅ Security issues identified"
echo -e "\n${YELLOW}🌐 Application URL: ${GREEN}${APP_URL}${NC}"
echo -e "\n${YELLOW}📖 Next Steps:${NC}"
echo -e "  1. Open Datadog and verify data is flowing"
echo -e "  2. Review the DEMO_GUIDE.md for detailed demo script"
echo -e "  3. Test the demo endpoints:"
echo -e "     • ${GREEN}${APP_URL}/api/health${NC} - Health check"
echo -e "     • ${GREEN}${APP_URL}/api/users/999${NC} - Runtime error"
echo -e "     • ${GREEN}${APP_URL}/vulnerable/123${NC} - Security vulnerability"
echo -e "\n${BLUE}📚 Demo Guide: ${NC}cat DEMO_GUIDE.md"
echo -e "${BLUE}🔧 Troubleshooting: ${NC}kubectl logs -f deployment/datadog-demo-app -n datadog-demo"

echo -e "\n${GREEN}🎯 Your Datadog demo environment is ready!${NC}"
