#!/bin/bash

# Datadog VS Code Extension Reset Script
# Clears cache, resets configuration, and forces reload

echo "🔄 Resetting Datadog VS Code Extension..."
echo ""

# Step 1: Stop the app if running
echo "1️⃣  Stopping any running Node processes..."
pkill -f "node.*app.js" || true
sleep 1

# Step 2: Clear Cursor/VSCode caches related to Datadog
echo "2️⃣  Clearing extension caches..."

# Remove Datadog extension cache
rm -rf ~/Library/Application\ Support/Cursor/User/globalStorage/datadog.datadog-vscode/ 2>/dev/null || true

# Remove Cursor logs related to Datadog extension
find ~/Library/Application\ Support/Cursor/logs -type f -path "*datadog*" -delete 2>/dev/null || true

echo "✅ Caches cleared"
echo ""

# Step 3: Display updated settings
echo "3️⃣  Verifying workspace settings..."
echo "📄 Workspace settings location: .vscode/settings.json"
echo ""

if [ -f .vscode/settings.json ]; then
    echo "Contents of .vscode/settings.json:"
    cat .vscode/settings.json | jq . 2>/dev/null || cat .vscode/settings.json
    echo ""
fi

# Step 4: Instructions for user
echo "4️⃣  Next steps:"
echo ""
echo "   a) Close Cursor completely:"
echo "      • Quit Cursor (⌘Q)"
echo ""
echo "   b) Reopen Cursor:"
echo "      • Open Cursor"
echo "      • Open /Users/eran.rahmani/datadog-demo-app folder"
echo ""
echo "   c) Verify Datadog extension:"
echo "      • Extensions panel (⌘⇧X)"
echo "      • Search for 'Datadog'"
echo "      • Check that extension is enabled"
echo ""
echo "   d) Start the demo app:"
echo "      • Open integrated terminal"
echo "      • Run: DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' npm start"
echo ""
echo "   e) Generate traffic:"
echo "      • In another terminal: for i in {1..10}; do curl http://localhost:3000/; done"
echo ""
echo "   f) Check log annotation:"
echo "      • Go back to src/app.js line 45 (Homepage accessed)"
echo "      • Hover over it and check the annotation"
echo "      • It should now show logs from 'datadog-demo-app' service"
echo ""

echo "✨ Extension reset complete!"
echo ""






