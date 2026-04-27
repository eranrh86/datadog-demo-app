#!/bin/bash

# Simple script to start the demo app and test it
echo "🚀 Starting Datadog Demo App..."

cd "$(dirname "$0")"

# Kill any existing node processes on port 3000
echo "Cleaning up any existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start the application in background
echo "Starting the application..."
NODE_ENV=development node src/app.js &
APP_PID=$!

# Wait for app to start
echo "Waiting for app to start..."
sleep 5

# Test the application
echo "Testing the application..."
node test-local.js

echo ""
echo "🎯 Demo app is running on http://localhost:3000"
echo "📊 Use these endpoints for your demo:"
echo "   • http://localhost:3000/ - Homepage"
echo "   • http://localhost:3000/api/health - Health check"
echo "   • http://localhost:3000/api/users/999 - Runtime error"
echo "   • http://localhost:3000/vulnerable/123 - Security vulnerability"
echo ""
echo "To stop the app: kill $APP_PID"
echo "Or run: lsof -ti:3000 | xargs kill -9"

