#!/bin/bash

# 🔄 Continuous Log & Trace Generator
# Generates logs and traces every 1 minute in the background

INTERVAL=60  # seconds (1 minute)
LOG_FILE="logs/traffic-generator.log"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🚀 Starting Continuous Log & Trace Generator          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Interval: $INTERVAL seconds (1 minute)"
echo "  Target: http://localhost:3000"
echo "  Log file: $LOG_FILE"
echo ""

# Check if app is running
if ! lsof -ti:3000 > /dev/null 2>&1; then
    echo "❌ App not running on port 3000"
    echo ""
    echo "Starting app now..."
    DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' \
    DD_SERVICE='datadog-demo-app' \
    DD_ENV='demo' \
    DD_VERSION='1.0.0' \
    NODE_ENV=development \
    nohup npm start > logs/app-runtime.log 2>&1 &
    
    echo "Waiting for app to start..."
    sleep 5
fi

echo "✅ App is running"
echo ""
echo "Starting traffic generation..."
echo "Press Ctrl+C to stop"
echo ""

# Counter
counter=0

# Function to generate traffic
generate_traffic() {
    local cycle=$1
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] Cycle #$cycle - Generating traffic..."
    
    # Homepage (3 requests)
    for i in {1..3}; do
        curl -s http://localhost:3000/ > /dev/null 2>&1
    done
    
    # Health check
    curl -s http://localhost:3000/api/health > /dev/null 2>&1
    
    # Users API (2 requests)
    curl -s http://localhost:3000/api/users > /dev/null 2>&1
    curl -s http://localhost:3000/api/users/1 > /dev/null 2>&1
    
    # Orders API (2 requests)
    curl -s http://localhost:3000/api/orders > /dev/null 2>&1
    
    # Generate an error (for error tracking)
    if [ $((cycle % 5)) -eq 0 ]; then
        curl -s http://localhost:3000/api/users/999 > /dev/null 2>&1
        echo "  ⚠️  Error trace generated"
    fi
    
    echo "  ✅ Generated 8+ logs & traces"
}

# Main loop
while true; do
    counter=$((counter + 1))
    generate_traffic $counter
    
    echo "  ⏰ Waiting $INTERVAL seconds until next cycle..."
    echo ""
    
    sleep $INTERVAL
done

