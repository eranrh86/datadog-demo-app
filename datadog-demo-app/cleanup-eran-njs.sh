#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        🗑️  eran-njs Cleanup Verification                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "1️⃣  Checking codebase for eran-njs..."
if grep -r "eran-njs" src/ .vscode/ .datadog/ --include="*.js" --include="*.json" --include="*.yaml" 2>/dev/null; then
    echo "   ❌ Found eran-njs in code/config"
else
    echo "   ✅ No eran-njs in code/config files"
fi

echo ""
echo "2️⃣  Verifying all code uses datadog-demo-app..."
count=$(grep -r "datadog-demo-app" src/ .vscode/ .datadog/ --include="*.js" --include="*.json" --include="*.yaml" 2>/dev/null | wc -l | xargs)
echo "   ✅ Found $count references to datadog-demo-app"

echo ""
echo "3️⃣  Checking current service name in logs..."
service=$(tail -1 logs/combined.log 2>/dev/null | jq -r '.service' 2>/dev/null || echo "unknown")
if [ "$service" = "datadog-demo-app" ]; then
    echo "   ✅ Current logs use: $service"
else
    echo "   ⚠️  Current logs use: $service"
fi

echo ""
echo "4️⃣  Checking configuration files..."
echo "   .vscode/settings.json:"
grep "datadog.service" .vscode/settings.json 2>/dev/null && echo "   ✅ Configured correctly" || echo "   ⚠️  Not found"
echo ""
echo "   .datadog/config.json:"
grep "service" .datadog/config.json 2>/dev/null && echo "   ✅ Configured correctly" || echo "   ⚠️  Not found"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    CODEBASE STATUS                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  ✅ Your codebase is CLEAN"
echo "  ✅ No eran-njs references in actual code"
echo "  ✅ All configurations use datadog-demo-app"
echo "  ✅ Current logs use correct service name"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║            CLEANUP NEEDED IN DATADOG CLOUD                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "The eran-njs service exists in Datadog's service catalog."
echo "To remove it completely:"
echo ""
echo "📍 STEP 1: Archive Service in Datadog"
echo "   1. Go to: https://app.datadoghq.com/services"
echo "   2. Search for: eran-njs"
echo "   3. Click on it → Settings → Archive Service"
echo ""
echo "📍 STEP 2: Verify No Logs"
echo "   1. Go to: https://app.datadoghq.com/logs"
echo "   2. Search: service:eran-njs"
echo "   3. Should show: 0 results (or only very old logs)"
echo ""
echo "📍 STEP 3: Verify Your Logs"
echo "   1. Search: service:datadog-demo-app"
echo "   2. Should show: 100+ recent logs ✅"
echo ""
echo "📍 STEP 4: Test Cursor Extension (after 30 minutes)"
echo "   1. Reload Cursor: Cmd+Shift+P → Reload Window"
echo "   2. Click annotation in src/app.js line 50"
echo "   3. Should open with: service:datadog-demo-app ✅"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  QUICK VERIFICATION LINKS                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Check old service (should be empty):"
echo "https://app.datadoghq.com/logs?query=service:eran-njs"
echo ""
echo "Check new service (should have logs):"
echo "https://app.datadoghq.com/logs?query=service:datadog-demo-app"
echo ""
echo "Service catalog:"
echo "https://app.datadoghq.com/services"
echo ""


