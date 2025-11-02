#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🔄 Force Refresh Cursor Datadog Extension             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "1️⃣  Clearing Datadog extension cache..."
rm -rf ~/Library/Application\ Support/Cursor/User/globalStorage/datadog.datadog-vscode/* 2>/dev/null
echo "   ✅ Extension cache cleared"

echo ""
echo "2️⃣  Clearing Cursor general cache..."
rm -rf ~/Library/Application\ Support/Cursor/Cache/* 2>/dev/null
rm -rf ~/Library/Application\ Support/Cursor/CachedData/* 2>/dev/null
echo "   ✅ General cache cleared"

echo ""
echo "3️⃣  Clearing Code Cache..."
rm -rf ~/Library/Application\ Support/Cursor/Code\ Cache/* 2>/dev/null
echo "   ✅ Code cache cleared"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    NEXT STEPS                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "1. CLOSE Cursor completely (Cmd+Q)"
echo "2. Wait 5 seconds"
echo "3. REOPEN Cursor"
echo "4. Open src/app.js line 50"
echo "5. Look for the annotation"
echo "6. Click it - should now use service:datadog-demo-app"
echo ""
echo "If still showing wrong service after this:"
echo "The extension has a fundamental limitation."
echo "Use the manual filter workaround:"
echo "  service:datadog-demo-app message:\"Homepage accessed\""
echo ""









