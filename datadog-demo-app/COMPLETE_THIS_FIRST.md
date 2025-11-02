# ⚡ QUICK START - DO THIS NOW

## The Problem
Your Cursor extension shows:
```
❌ "No log events in the past day"
🔗 Links to: service:(eran-njs) [0 logs]
```

But your actual logs are in:
```
✅ service:datadog-demo-app [15+ logs]
```

## The Fix (Already Applied) ✅
I've configured:
- ✅ Cursor global settings
- ✅ Workspace settings (.vscode/settings.json)
- ✅ Datadog configuration (datadog.yaml)
- ✅ Cleared extension cache
- ✅ Generated 15+ fresh logs

## What You Need to Do Right Now

### Step 1: Close Cursor (1 minute)
```
Press: ⌘Q
(Fully quit Cursor)
```

### Step 2: Reopen Cursor (1 minute)
```
1. Launch Cursor again
2. Open folder: /Users/eran.rahmani/datadog-demo-app
3. Wait 10 seconds for workspace to load
```

### Step 3: Start the App (1 minute)
```bash
# In Cursor terminal:
DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' npm start
```

Expected output:
```
✅ Datadog HTTP transport configured
info: Server started on port 3000
```

### Step 4: Generate Traffic (1 minute)
```bash
# In a NEW terminal:
cd /Users/eran.rahmani/datadog-demo-app
for i in {1..10}; do curl -s http://localhost:3000/ > /dev/null; echo "Request $i"; done
```

### Step 5: Check the Annotation (1 minute)
```
1. Go to src/app.js
2. Look at line 45 (the logger.info('Homepage accessed' line)
3. Hover over it
```

## Expected Result
Instead of:
```
❌ No log events in the past day
```

You should see:
```
✅ 15 logs in the past hour
🔗 Link to: service:datadog-demo-app message:"Homepage accessed"
```

## Total Time: 5 Minutes ⏱️

---

## If Something Goes Wrong

### The annotation still shows the wrong service?
```bash
# Try this:
cd /Users/eran.rahmani/datadog-demo-app
./RESET_DATADOG_EXTENSION.sh
```
Then:
1. Close Cursor (⌘Q)
2. Reopen Cursor
3. Retry

### Not seeing 10 logs generated?
```bash
# Verify app is running:
curl http://localhost:3000/ | jq .

# If it fails, restart:
pkill -f "node.*app.js"
DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' npm start
```

### Logs exist locally but not in annotation?
Check if Datadog received them:
1. Go to: https://app.datadoghq.com/logs
2. Use filter: `service:datadog-demo-app message:"Homepage accessed"`
3. Set time: Last 30 minutes
4. Should show 15+ logs

---

## Files That Were Changed

```
✅ ~/.../Cursor/User/settings.json
   Added Datadog service configuration

✅ .vscode/settings.json (NEW)
   Workspace-level settings for this project

✅ datadog.yaml (NEW)
   Explicit service configuration

✅ RESET_DATADOG_EXTENSION.sh (NEW)
   Helper script to clear cache if needed
```

---

## That's It!
🚀 **The hardest part is done. Now just restart Cursor and the extension should work!**

Need detailed help? See: `FIX_CURSOR_EXTENSION.md`






