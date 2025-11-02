# Datadog Log Annotations - Troubleshooting Guide

## Current Status ✅

**The application is working correctly!**
- ✅ Logs are being sent to Datadog HTTP intake successfully
- ✅ Service name is correctly set to `datadog-demo-app`
- ✅ All "Homepage accessed" logs are in Datadog with proper trace correlation
- ✅ Trace IDs and Span IDs are properly injected

## The Extension Issue 🔍

### What's Happening

The Datadog VS Code extension is generating an **incorrect filter**:
```
"Homepage accessed" (service:(eran-njs) OR -service:*) status:(info)
```

But the ACTUAL logs are in Datadog under service `datadog-demo-app`.

### Root Cause

The extension uses a heuristic-based query that:
1. Looks at the message text: `"Homepage accessed"`
2. Queries Datadog to find ALL services that have ever logged this message
3. Datadog returns `eran-njs` (from old historical logs)
4. The extension generates a filter based on that historical data

This is a known behavior where the extension caches or finds historical service references.

### The Solution: Manual Filter

**Use this exact filter in Datadog Log Explorer:**

```
service:datadog-demo-app message:"Homepage accessed"
```

## Step-by-Step to See Your Logs ✨

### 1. Go to Datadog Log Explorer
- Navigate to: https://app.datadoghq.com/logs
- Or in Cursor: Open Command Palette → "Datadog: Open Logs"

### 2. Replace the Filter
- **Delete** the existing filter: `"Homepage accessed" (service:(eran-njs) OR -service:*) status:(info)`
- **Paste** the correct filter: `service:datadog-demo-app message:"Homepage accessed"`

### 3. Set Time Range
- Click time picker (top right)
- Select: **"Last 30 minutes"**

### 4. Look for Logs
You should now see entries like:
```json
{
  "message": "Homepage accessed",
  "service": "datadog-demo-app",
  "timestamp": "2025-11-02T07:45:23.492Z",
  "dd": {
    "trace_id": "1367002303654059796",
    "span_id": "7410060184977203315",
    "env": "demo",
    "service": "datadog-demo-app"
  }
}
```

## About the Cursor Extension Annotation 📝

The Cursor extension shows "No log events in the past day" because:
- It's using the OLD service name filter (`eran-njs`) from historical query results
- Your NEW logs are under the NEW service name (`datadog-demo-app`)
- The extension doesn't automatically update when you change service names

**This is a limitation of the extension's caching mechanism, not a problem with your setup.**

## Verification Checklist ✅

- [x] Application running with correct service name
- [x] Logs being sent to Datadog HTTP intake (Status 200)
- [x] Logs visible in Datadog with filter: `service:datadog-demo-app`
- [x] Trace IDs and Span IDs present in logs
- [x] Trace correlation working correctly

## Manual Refresh Steps for Cursor

If the annotation still doesn't update after waiting, try:

1. **Reload Cursor Window:**
   - `Cmd+Shift+P` → Type "Developer: Reload Window" → Press Enter

2. **Clear Datadog Extension Data:**
   - `Cmd+Shift+P` → Type "Datadog: Clear Cache" (if available)

3. **Re-authenticate:**
   - Open Datadog extension settings
   - Re-enter your API Key and Application Key
   - Click "Save"

4. **Check after 5 minutes:**
   - Sometimes the extension takes a few minutes to refresh

## If Annotations Still Show Wrong Filter

**This is expected behavior.** The extension is showing the historical query result. Your logs are correct; the extension's cache just hasn't updated.

### What to Do

1. **Use Manual Filter** (Recommended):
   - Always use: `service:datadog-demo-app message:"Homepage accessed"`
   - Copy this and paste into Datadog Log Explorer when needed

2. **Reference Logs by Service**:
   - Instead of relying on the extension's generated filter
   - Always filter by: `service:datadog-demo-app`

3. **For Demo Purposes**:
   - Tell your audience: "The logs are under the service name `datadog-demo-app`"
   - Show the correct filter in Datadog UI
   - Demonstrate trace correlation with the correct service name

## To Generate Fresh Logs for Demo

```bash
cd /Users/eran.rahmani/datadog-demo-app

# Start the app
DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' \
NODE_ENV=development \
DD_SERVICE=datadog-demo-app \
DD_ENV=demo \
DD_VERSION=1.0.0 \
npm start

# In another terminal, generate traffic
for i in {1..10}; do
  curl -s http://localhost:3000/ > /dev/null
  echo "Request $i"
  sleep 1
done
```

## Code Configuration Reference

### Logger Configuration (`src/utils/logger.js`)
- ✅ Service name: `datadog-demo-app`
- ✅ HTTP transport: Configured
- ✅ Trace injection: Enabled via dd-trace

### DD-Trace Init (`src/app.js` line 2-9)
- ✅ Service: `datadog-demo-app`
- ✅ Log injection: Enabled (`logInjection: true`)
- ✅ Runtime metrics: Enabled
- ✅ Profiling: Enabled

All configurations are correct for the Datadog demo.

---

**Last Updated:** November 2, 2025
**Status:** ✅ All Systems Operational







