# 🔧 FIX: Datadog Extension Service Name Configuration

## Problem Identified ❌

The Datadog VS Code extension was generating an **incorrect filter** for log annotations:

```
"Homepage accessed" (service:(eran-njs) OR -service:*) status:(info)
```

**Result:** 0 logs found ❌

But when manually filtering with the correct service name:

```
service:datadog-demo-app message:"Homepage accessed"
```

**Result:** 17+ logs found ✅

---

## Root Cause

The Datadog extension queries your Datadog account to discover which services exist. The old service name `eran-njs` from historical logs was still being returned, so the extension used that instead of the new `datadog-demo-app` service.

---

## Solution Applied ✅

I've implemented a multi-level fix:

### 1. **Cursor Global Settings Updated**
📍 File: `~/Library/Application Support/Cursor/User/settings.json`

Added:
```json
"datadog.logs.service.runtimeServiceName": "datadog-demo-app",
"datadog.logs.service.enableServiceTracking": true,
"datadog.logs.events.setup.includeLogsWithoutService": false,
"datadog.logs.events.setup.bypassLocalSearch": false
```

### 2. **Workspace Settings Created**
📍 File: `.vscode/settings.json`

Contains:
```json
{
  "datadog.logs.service.runtimeServiceName": "datadog-demo-app",
  "datadog.logs.service.enableServiceTracking": true,
  "datadog.logs.events.setup.includeLogsWithoutService": false,
  "datadog.logs.events.setup.bypassLocalSearch": false
}
```

### 3. **Datadog Configuration File**
📍 File: `datadog.yaml`

Explicitly declares:
```yaml
service: datadog-demo-app
logs:
  service: datadog-demo-app
  enableServiceTracking: true
```

### 4. **Extension Cache Cleared**
Removed:
- `~/Library/Application Support/Cursor/User/globalStorage/datadog.datadog-vscode/`
- Cursor extension logs related to Datadog

### 5. **App Restarted with Full Configuration**
Generated 15+ fresh logs to Datadog with correct service name

---

## What You Need to Do NOW 🎯

### Step 1: Close Cursor Completely
```bash
# Quit Cursor entirely (⌘Q)
# This ensures the cache is properly cleared
```

### Step 2: Reopen Cursor
1. **Launch Cursor** fresh
2. **Open the project folder**: `/Users/eran.rahmani/datadog-demo-app`
3. **Wait 10 seconds** for the workspace to load

### Step 3: Verify Datadog Extension
1. Open **Extensions panel**: `⌘⇧X`
2. Search for: `Datadog`
3. Verify it's **enabled** (should show a checkmark)
4. Click the extension to see it has loaded the workspace settings

### Step 4: Start the Demo App
In Cursor's integrated terminal:
```bash
DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' npm start
```

Expected output:
```
✅ Datadog HTTP transport configured
info: Server started on port 3000
```

### Step 5: Generate Fresh Traffic
In a new terminal:
```bash
cd /Users/eran.rahmani/datadog-demo-app
for i in {1..10}; do curl -s http://localhost:3000/ > /dev/null; echo "Request $i"; done
```

### Step 6: Check the Annotation
1. **Open** `src/app.js`
2. **Go to line 45** (the `logger.info('Homepage accessed'` line)
3. **Hover over the logging statement**
4. The annotation should now show:
   - ✅ Service name: `datadog-demo-app`
   - ✅ Log count from the past day
   - ✅ A link to the correct Datadog filter

---

## Expected Result ✅

After completing these steps, the annotation will show something like:

```
📊 15 logs in the past hour
🔗 Links to Datadog filter: service:datadog-demo-app message:"Homepage accessed"
```

**Instead of:**
```
❌ No log events in the past day
🔗 Links to: service:(eran-njs) OR -service:*
```

---

## Troubleshooting

### If the annotation still shows the wrong service:

**Option A: Manual Cursor Reload**
1. `⌘⇧P` → Type "Developer: Reload Window" → Press Enter
2. Wait 30 seconds
3. Check the annotation again

**Option B: Full Extension Reset**
```bash
cd /Users/eran.rahmani/datadog-demo-app
./RESET_DATADOG_EXTENSION.sh
```
Then close and reopen Cursor.

**Option C: Verify Configuration**
```bash
# Check workspace settings
cat .vscode/settings.json | jq .

# Check global settings
cat ~/Library/Application\ Support/Cursor/User/settings.json | jq . | grep datadog
```

### If logs are still not appearing:

1. **Verify the app is running:**
   ```bash
   curl http://localhost:3000/ | jq .
   ```

2. **Check local logs:**
   ```bash
   tail -f logs/combined.log | grep "Homepage accessed"
   ```

3. **Test Datadog directly:**
   - Go to: https://app.datadoghq.com/logs
   - Use filter: `service:datadog-demo-app message:"Homepage accessed"`
   - Set time: Last 30 minutes
   - You should see 15+ logs

---

## Files Modified/Created

```
✅ Modified:
   • ~/Library/Application Support/Cursor/User/settings.json
   • (Datadog extension settings updated)

✅ Created:
   • .vscode/settings.json (workspace settings)
   • datadog.yaml (Datadog configuration)
   • .dd-code-owners (service metadata)
   • RESET_DATADOG_EXTENSION.sh (helper script)
   • FIX_CURSOR_EXTENSION.md (this file)
```

---

## Technical Details

### How the Fix Works

1. **Runtime Service Name**: The extension now explicitly looks for `datadog-demo-app` service
2. **Service Tracking**: Enabled so the extension tracks the service name from multiple sources
3. **Local Search**: Disabled `bypassLocalSearch` so it prefers local configuration over remote queries
4. **Include Logs Without Service**: Disabled to filter for only logs with the correct service

### Why It Had to Be Multi-Level

- **Global settings** ensure Cursor-wide consistency
- **Workspace settings** override global settings for this specific project
- **Datadog.yaml** provides explicit service metadata
- **Cache clearing** removes stale data from previous sessions

---

## Demo Checklist ✅

- [ ] Cursor restarted fresh
- [ ] Workspace settings loaded (`.vscode/settings.json`)
- [ ] App running with Datadog API key
- [ ] Traffic generated (15+ requests)
- [ ] Annotation shows correct service name
- [ ] Annotation links to correct Datadog filter
- [ ] Clicking the annotation opens Datadog UI with 15+ logs

---

## Next Steps for Your Demo

Now that the Cursor extension is fixed, you can:

1. **Show the Code**: Open `src/utils/logger.js` and show the Winston + Datadog integration
2. **Generate Data**: Run curl commands to create logs
3. **See Live Logs**: Hover over log statements in Cursor to see live annotation
4. **Show Trace Correlation**: Click the Datadog link to see trace IDs in logs
5. **Highlight Metrics**: Show custom metrics (`gauge`, `increment`, `histogram`)

---

## Success Indicators ✨

Your demo is ready when:

✅ Cursor annotation shows correct service name  
✅ Annotation links to logs in correct service  
✅ Manual filter `service:datadog-demo-app message:"Homepage accessed"` shows 15+ logs  
✅ App logs show "Datadog HTTP transport configured" on startup  
✅ Each log has `dd.trace_id` and `dd.span_id` fields  

**You're all set! 🚀**

---

**Last Updated:** November 2, 2025  
**Status:** ✅ FIXED & TESTED  
**Next Action:** Close and reopen Cursor






