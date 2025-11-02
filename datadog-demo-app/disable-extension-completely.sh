#!/bin/bash

# Complete Datadog Extension Disable Script

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🔴 COMPLETELY DISABLE DATADOG EXTENSION               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "Step 1: Disabling all Datadog features in settings..."
cat > .vscode/settings.json << 'JSON'
{
  "datadog.site": "datadoghq.com",
  "datadog.apiKey": "",
  "datadog.logs.service.runtimeServiceName": "datadog-demo-app",
  "datadog.logs.service.enableServiceTracking": false,
  "datadog.logs.events.setup.includeLogsWithoutService": false,
  "datadog.logs.events.setup.bypassLocalSearch": false,
  "datadog.logs.events.enabled": false,
  "datadog.logs.events.setup.autoRefresh": false,
  "datadog.service": "datadog-demo-app",
  "datadog.env": "demo",
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
JSON

echo "✅ Settings updated"
echo ""

echo "Step 2: Clearing all Datadog extension data..."
rm -rf ~/Library/Application\ Support/Cursor/User/globalStorage/datadog.datadog-vscode/* 2>/dev/null
echo "✅ Extension data cleared"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                 CRITICAL: RESTART CURSOR NOW               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Close Cursor completely: Cmd + Q"
echo "2. Wait 5 seconds"
echo "3. Reopen Cursor"
echo "4. Open src/app.js"
echo "5. Line 50 should have NO annotation"
echo ""
echo "If annotation STILL shows after this:"
echo "→ We need to uninstall the extension completely"
echo ""






