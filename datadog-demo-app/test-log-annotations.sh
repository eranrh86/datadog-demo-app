#!/bin/bash

# 🔥 Test Log Annotations in Cursor
# This script generates logs and verifies the Datadog integration

echo "🚀 Testing Datadog Log Annotations..."
echo ""

# Check if app is running
if lsof -ti:3000 > /dev/null 2>&1; then
    echo "✅ App is running on port 3000"
else
    echo "❌ App is not running. Starting it now..."
    DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' \
    DD_SERVICE='datadog-demo-app' \
    DD_ENV='demo' \
    DD_VERSION='1.0.0' \
    NODE_ENV=development \
    nohup npm start > logs/app-runtime.log 2>&1 &
    
    echo "Waiting for app to start..."
    sleep 5
fi

echo ""
echo "📝 Generating logs for annotations..."
echo ""

# Generate homepage logs (line 50 in src/app.js)
echo "1. Homepage logs (should appear at line 50 in src/app.js):"
for i in {1..10}; do
    curl -s http://localhost:3000/ > /dev/null
    echo "   ✓ Homepage request $i"
    sleep 0.3
done

echo ""
echo "2. Users API logs (should appear at line 16 in src/routes/users.js):"
for i in {1..10}; do
    curl -s http://localhost:3000/api/users > /dev/null
    echo "   ✓ Users API request $i"
    sleep 0.3
done

echo ""
echo "3. Orders API logs (should appear at line 14 in src/routes/orders.js):"
for i in {1..10}; do
    curl -s http://localhost:3000/api/orders > /dev/null
    echo "   ✓ Orders API request $i"
    sleep 0.3
done

echo ""
echo "4. Health Check logs (should appear at line 8 in src/routes/health.js):"
for i in {1..5}; do
    curl -s http://localhost:3000/api/health > /dev/null
    echo "   ✓ Health check $i"
    sleep 0.3
done

echo ""
echo "✅ Log generation complete!"
echo ""
echo "📊 Statistics:"
echo "   - Homepage: 10 logs"
echo "   - Users API: 10 logs"
echo "   - Orders API: 10 logs"
echo "   - Health API: 5 logs"
echo "   - Total: 35 new logs"
echo ""
echo "🔍 Where to find annotations in Cursor:"
echo ""
echo "   1. src/app.js (line 50)"
echo "      logger.info('Homepage accessed', {"
echo ""
echo "   2. src/routes/users.js (line 16)"
echo "      logger.info('Fetching all users', {"
echo ""
echo "   3. src/routes/orders.js (line 14)"
echo "      logger.info('Fetching all orders', {"
echo ""
echo "   4. src/routes/health.js (line 8)"
echo "      logger.info('Health check performed', {"
echo ""
echo "⏳ Next steps:"
echo "   1. Reload Cursor window (Cmd+Shift+P → 'Developer: Reload Window')"
echo "   2. Wait 2-3 minutes for Datadog to process logs"
echo "   3. Open the files above and look for gray text annotations"
echo "   4. Click an annotation to open Datadog Log Explorer"
echo ""
echo "🌐 Manual verification:"
echo "   Visit: https://app.datadoghq.com/logs"
echo "   Filter: service:datadog-demo-app"
echo ""
echo "✨ Done!"

