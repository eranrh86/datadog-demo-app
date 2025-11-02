#!/bin/bash

# Datadog Source Code Integration - Build and Deploy Script
# This script builds the Docker image with Git metadata for Datadog APM

set -e

echo "🐕 Datadog Source Code Integration - Build Script"
echo "=================================================="

# Get Git metadata
GIT_REPOSITORY_URL=$(git config --get remote.origin.url)
GIT_COMMIT_SHA=$(git rev-parse HEAD)

echo "📦 Git Repository: $GIT_REPOSITORY_URL"
echo "📍 Commit SHA: $GIT_COMMIT_SHA"
echo ""

# Build Docker image with Git metadata
echo "🔨 Building Docker image with Git metadata..."
docker build . \
  -t datadog-demo-app:latest \
  --build-arg DD_GIT_REPOSITORY_URL="$GIT_REPOSITORY_URL" \
  --build-arg DD_GIT_COMMIT_SHA="$GIT_COMMIT_SHA"

echo ""
echo "✅ Docker image built successfully!"
echo ""
echo "📝 Next steps:"
echo "1. For Docker deployment:"
echo "   docker run -d -p 3000:3000 \\"
echo "     -e DD_API_KEY=your_api_key \\"
echo "     datadog-demo-app:latest"
echo ""
echo "2. For Kubernetes deployment:"
echo "   - Update k8s/deployment.yaml DD_GIT_COMMIT_SHA with: $GIT_COMMIT_SHA"
echo "   - Run: kubectl apply -f k8s/"
echo ""
echo "3. Verify in Datadog:"
echo "   - Go to APM > Services > datadog-demo-app"
echo "   - Click on any trace > View in IDE"
echo "   - Should jump directly to source code!"

