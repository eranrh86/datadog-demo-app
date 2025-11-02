#!/bin/bash

# 🗑️ Delete eran-njs Service from Datadog
# Uses Datadog API v2 to delete service definition

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🗑️  Delete eran-njs Service from Datadog              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Get API key from config
DD_API_KEY="be9f47b60fedd8042065bd3052eb546e"
DD_SITE="datadoghq.com"

# Note: Service deletion typically requires an Application Key
# You'll need to create one at: https://app.datadoghq.com/organization-settings/application-keys

echo "📋 Configuration:"
echo "   API Key: ${DD_API_KEY:0:20}..."
echo "   Site: $DD_SITE"
echo "   Service to delete: eran-njs"
echo ""

# Check if APP_KEY is provided
if [ -z "$DD_APP_KEY" ]; then
    echo "⚠️  Application Key Required"
    echo ""
    echo "To delete a service, you need a Datadog Application Key."
    echo ""
    echo "📍 Get your Application Key:"
    echo "   1. Go to: https://app.datadoghq.com/organization-settings/application-keys"
    echo "   2. Click 'New Key'"
    echo "   3. Name it: 'Service Management'"
    echo "   4. Copy the key"
    echo ""
    echo "📍 Then run this script with:"
    echo "   DD_APP_KEY='your-app-key' ./delete-eran-njs-service.sh"
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              ALTERNATIVE: MANUAL DELETION                  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "You can also delete manually in the UI:"
    echo "1. Go to: https://app.datadoghq.com/services"
    echo "2. Search: eran-njs"
    echo "3. Click → Settings → Archive/Delete"
    echo ""
    exit 1
fi

echo "🔍 Step 1: Verifying service exists..."
echo ""

# Try to get the service first
response=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://api.$DD_SITE/api/v2/services/definitions/eran-njs" \
    -H "DD-API-KEY: $DD_API_KEY" \
    -H "DD-APPLICATION-KEY: $DD_APP_KEY")

if [ "$response" = "404" ]; then
    echo "✅ Service 'eran-njs' not found in Datadog"
    echo "   (Already deleted or never existed)"
    echo ""
    echo "Verifying current service..."
    curl -s "https://api.$DD_SITE/api/v2/services/definitions/datadog-demo-app" \
        -H "DD-API-KEY: $DD_API_KEY" \
        -H "DD-APPLICATION-KEY: $DD_APP_KEY" | jq -r '.data.attributes.schema."schema-version"' 2>/dev/null && echo "✅ datadog-demo-app exists" || echo ""
    exit 0
elif [ "$response" = "200" ]; then
    echo "⚠️  Service 'eran-njs' found"
    echo ""
else
    echo "❌ Unexpected response: $response"
    echo "   Check your API/APP keys"
    exit 1
fi

echo "🗑️  Step 2: Deleting service 'eran-njs'..."
echo ""

# Delete the service
delete_response=$(curl -s -w "\n%{http_code}" \
    -X DELETE \
    "https://api.$DD_SITE/api/v2/services/definitions/eran-njs" \
    -H "DD-API-KEY: $DD_API_KEY" \
    -H "DD-APPLICATION-KEY: $DD_APP_KEY")

http_code=$(echo "$delete_response" | tail -n1)
response_body=$(echo "$delete_response" | sed '$d')

if [ "$http_code" = "204" ] || [ "$http_code" = "200" ]; then
    echo "✅ Service 'eran-njs' deleted successfully!"
    echo ""
elif [ "$http_code" = "404" ]; then
    echo "✅ Service 'eran-njs' not found (already deleted)"
    echo ""
else
    echo "❌ Failed to delete service"
    echo "   HTTP Code: $http_code"
    echo "   Response: $response_body"
    echo ""
    exit 1
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    VERIFICATION                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Wait a moment for propagation
echo "Waiting 5 seconds for changes to propagate..."
sleep 5

echo ""
echo "🔍 Checking service catalog..."

# Verify deletion
verify_response=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://api.$DD_SITE/api/v2/services/definitions/eran-njs" \
    -H "DD-API-KEY: $DD_API_KEY" \
    -H "DD-APPLICATION-KEY: $DD_APP_KEY")

if [ "$verify_response" = "404" ]; then
    echo "✅ Confirmed: eran-njs no longer in service catalog"
else
    echo "⚠️  Service might still be cached (code: $verify_response)"
    echo "   Wait 10-15 minutes for full propagation"
fi

echo ""
echo "✅ Checking datadog-demo-app exists..."
current_service=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://api.$DD_SITE/api/v2/services/definitions/datadog-demo-app" \
    -H "DD-API-KEY: $DD_API_KEY" \
    -H "DD-APPLICATION-KEY: $DD_APP_KEY")

if [ "$current_service" = "200" ]; then
    echo "✅ datadog-demo-app is active"
else
    echo "⚠️  datadog-demo-app response: $current_service"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    NEXT STEPS                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Wait 15-30 minutes for Datadog to fully propagate changes"
echo ""
echo "2. Verify in UI:"
echo "   https://app.datadoghq.com/services"
echo "   → Search 'eran-njs' should show nothing"
echo ""
echo "3. Reload Cursor:"
echo "   Cmd+Shift+P → 'Developer: Reload Window'"
echo ""
echo "4. Test log annotations:"
echo "   Open src/app.js line 50"
echo "   Click annotation"
echo "   Should open with: service:datadog-demo-app ✅"
echo ""
echo "🎉 Done!"


