#!/bin/bash

# Datadog Demo App Deployment Script for Minikube
set -e

echo "🚀 Deploying Datadog Demo App to Minikube..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if minikube is running
echo -e "${BLUE}Checking minikube status...${NC}"
if ! minikube status > /dev/null 2>&1; then
    echo -e "${RED}Minikube is not running. Please start minikube first.${NC}"
    echo "Run: minikube start --profile eran-k8"
    exit 1
fi

# Switch to the correct minikube profile
echo -e "${BLUE}Switching to eran-k8 profile...${NC}"
minikube profile eran-k8

# Build Docker image and load into minikube
echo -e "${BLUE}Building Docker image...${NC}"
cd "$(dirname "$0")/.."  # Ensure we're in the project root

# Build image locally first
docker build -t datadog-demo-app:latest .

# Load image into minikube
echo -e "${BLUE}Loading image into minikube...${NC}"
minikube image load datadog-demo-app:latest

# Create namespace
echo -e "${BLUE}Creating namespace...${NC}"
kubectl apply -f k8s/namespace.yaml

# Apply ConfigMap
echo -e "${BLUE}Applying ConfigMap...${NC}"
kubectl apply -f k8s/configmap.yaml

# Deploy application
echo -e "${BLUE}Deploying application...${NC}"
kubectl apply -f k8s/deployment.yaml

# Wait for deployment to be ready
echo -e "${BLUE}Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/datadog-demo-app -n datadog-demo

# Get service URL
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Application URLs:${NC}"

MINIKUBE_IP=$(minikube ip)
NODE_PORT=$(kubectl get svc datadog-demo-service -n datadog-demo -o jsonpath='{.spec.ports[0].nodePort}')

echo -e "  Main App: ${GREEN}http://${MINIKUBE_IP}:${NODE_PORT}${NC}"
echo -e "  Health Check: ${GREEN}http://${MINIKUBE_IP}:${NODE_PORT}/api/health${NC}"
echo -e "  Users API: ${GREEN}http://${MINIKUBE_IP}:${NODE_PORT}/api/users${NC}"
echo -e "  Orders API: ${GREEN}http://${MINIKUBE_IP}:${NODE_PORT}/api/orders${NC}"

echo -e "\n${YELLOW}Demo Endpoints for Datadog Features:${NC}"
echo -e "  Runtime Error: ${GREEN}http://${MINIKUBE_IP}:${NODE_PORT}/error/runtime${NC}"
echo -e "  Vulnerable Endpoint: ${GREEN}http://${MINIKUBE_IP}:${NODE_PORT}/vulnerable/123${NC}"
echo -e "  Memory Leak: ${GREEN}http://${MINIKUBE_IP}:${NODE_PORT}/memory-leak${NC}"
echo -e "  User Error (999): ${GREEN}http://${MINIKUBE_IP}:${NODE_PORT}/api/users/999${NC}"
echo -e "  Order Error (666): ${GREEN}http://${MINIKUBE_IP}:${NODE_PORT}/api/orders/666${NC}"

echo -e "\n${YELLOW}Kubernetes Commands:${NC}"
echo -e "  View pods: ${BLUE}kubectl get pods -n datadog-demo${NC}"
echo -e "  View logs: ${BLUE}kubectl logs -f deployment/datadog-demo-app -n datadog-demo${NC}"
echo -e "  Port forward: ${BLUE}kubectl port-forward svc/datadog-demo-service 3000:80 -n datadog-demo${NC}"

echo -e "\n${GREEN}✅ Deployment complete! Your demo app is ready for Datadog integration.${NC}"
