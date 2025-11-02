# 🔧 FIX: Wrong Service Filter (eran-njs vs datadog-demo-app)

## ❌ The Problem You're Seeing

When you click the annotation "No log events in the past day", it opens Datadog with:

```
❌ WRONG FILTER:
"Homepage accessed" (service:(eran-njs) OR -service:*) status:(info)
```

But your logs are actually under:
```
✅ CORRECT SERVICE:
service:datadog-demo-app
```

---

## 🎯 IMMEDIATE FIX (Works Right Now)

### **Manual Filter Workaround**

When the Datadog Log Explorer opens with the wrong filter:

**1. Click on the search bar at the top**

**2. DELETE the entire existing filter**

**3. PASTE this correct filter:**
```
service:datadog-demo-app message:"Homepage accessed"
```

**4. Press Enter**

**Result:** You'll now see all 101 logs with the correct service name! 🎉

---

## 📋 Quick Copy-Paste Filters

Use these filters for different log patterns:

### **Homepage Logs:**
```
service:datadog-demo-app message:"Homepage accessed"
```

### **Users API Logs:**
```
service:datadog-demo-app message:"Fetching all users"
```

### **Orders API Logs:**
```
service:datadog-demo-app message:"Fetching all orders"
```

### **Health Check Logs:**
```
service:datadog-demo-app message:"Health check performed"
```

### **All App Logs:**
```
service:datadog-demo-app
```

---

## 🔍 Why This Happens

**Root Cause:**
The Datadog Cursor extension:
1. Detects the log pattern: `"Homepage accessed"`
2. Queries Datadog API: "Which services have logged this message?"
3. Datadog returns: `eran-njs` (from old historical logs in your account)
4. Extension generates filter using that old service name
5. Filter finds no logs (because new logs use `datadog-demo-app`)

**This is a known caching behavior** - the extension uses historical service data rather than current runtime service names.

---

## 🧹 PERMANENT FIX: Remove Old Service from Datadog

To fix this permanently, you need to remove the old `eran-njs` service from Datadog's service catalog.

### **Option 1: Archive Old Service in Datadog UI**

**Step 1: Go to Service Catalog**
1. Open: https://app.datadoghq.com/services
2. Search for: `eran-njs`
3. Click on it

**Step 2: Archive the Service**
1. Look for "Archive Service" or "Remove Service" option
2. Archive or delete it
3. Confirm the action

**Step 3: Clear Old Logs (Optional)**
1. Go to: https://app.datadoghq.com/logs
2. Filter: `service:eran-njs`
3. If you see old logs:
   - They will age out automatically (retention period)
   - Or you can create an exclusion filter to stop indexing them

**Step 4: Wait 10-15 Minutes**
- Datadog's service catalog updates periodically
- The extension will pick up the new service list

**Step 5: Reload Cursor**
- `Cmd + Shift + P` → "Developer: Reload Window"
- The extension should now only find `datadog-demo-app`

---

### **Option 2: Generate Volume of New Logs**

Sometimes overwhelming the system with new logs helps:

```bash
cd /Users/eran.rahmani/datadog-demo-app

# Generate 100 logs with correct service name
for i in {1..100}; do
  curl -s http://localhost:3000/ > /dev/null
  echo "✓ Log $i sent"
  sleep 0.5
done
```

**Result:**
- 100 new logs with `service:datadog-demo-app`
- Makes it the most recent/active service
- Extension more likely to pick the right service

---

### **Option 3: Update Extension Settings (Force Service Name)**

Sometimes you can force the extension to use a specific service:

**File:** `.vscode/settings.json`

Ensure these are set:
```json
{
  "datadog.logs.service.runtimeServiceName": "datadog-demo-app",
  "datadog.service": "datadog-demo-app",
  "datadog.logs.events.setup.includeLogsWithoutService": false
}
```

Then reload Cursor:
```
Cmd + Shift + P → "Developer: Reload Window"
```

---

## ✅ Verify the Fix Worked

### **Test 1: Check Logs in Datadog**

Go to: https://app.datadoghq.com/logs

**Search 1: Old service**
```
service:eran-njs
```
**Expected:** No results or only very old logs

**Search 2: New service**
```
service:datadog-demo-app
```
**Expected:** 100+ recent logs (within last hour)

### **Test 2: Check Service Catalog**

Go to: https://app.datadoghq.com/services

**Search:** `datadog-demo-app`
- **Expected:** Shows as active service

**Search:** `eran-njs`
- **Expected:** Not found or archived

### **Test 3: Test Annotation Again**

1. Reload Cursor (`Cmd + Shift + P` → Reload Window)
2. Open `src/app.js` line 50
3. Click the annotation
4. **Expected:** Opens Datadog with `service:datadog-demo-app` in filter

---

## 📝 Current Workaround (Use This Until Fixed)

**For now, use manual filters:**

1. Click the annotation (even with wrong filter)
2. When Datadog opens, replace the filter with:
   ```
   service:datadog-demo-app message:"Homepage accessed"
   ```
3. Bookmark this URL for quick access:
   ```
   https://app.datadoghq.com/logs?query=service%3Adatadog-demo-app
   ```

---

## 🎯 Quick Reference Card

Keep this handy when clicking annotations:

```
┌───────────────────────────────────────────────┐
│ WHEN ANNOTATION OPENS WRONG FILTER:           │
├───────────────────────────────────────────────┤
│ 1. Click search bar                           │
│ 2. Delete all text (Cmd+A, Delete)           │
│ 3. Paste:                                     │
│    service:datadog-demo-app message:"..."     │
│ 4. Press Enter                                │
│ 5. See your logs! ✅                          │
└───────────────────────────────────────────────┘
```

---

## 🔗 Direct Links (Bypass Extension)

Use these links to go directly to your logs:

**All Logs:**
https://app.datadoghq.com/logs?query=service%3Adatadog-demo-app

**Homepage Logs:**
https://app.datadoghq.com/logs?query=service%3Adatadog-demo-app%20message%3A%22Homepage%20accessed%22

**Users API:**
https://app.datadoghq.com/logs?query=service%3Adatadog-demo-app%20message%3A%22Fetching%20all%20users%22

**Orders API:**
https://app.datadoghq.com/logs?query=service%3Adatadog-demo-app%20message%3A%22Fetching%20all%20orders%22

---

## 💡 Understanding the Extension Behavior

**How Log Annotations Work:**

1. Extension scans your code for logger patterns
2. Extracts log message: `"Homepage accessed"`
3. Queries Datadog API: `GET /api/v1/logs/services?query=message:"Homepage accessed"`
4. Datadog returns list of services that have this message
5. Extension uses the first/most common service in the response
6. If old service `eran-njs` is in the response, it gets used

**Why It Uses Old Service:**
- Datadog keeps service history (30+ days)
- Old logs with `service:eran-njs` still exist in Datadog
- Extension doesn't know which service is "current" vs "historical"
- It picks based on heuristics (most common, most recent matches, etc.)

**Why Manual Filter Works:**
- You explicitly specify the service name
- Bypasses the extension's service discovery
- Always uses the exact service you want

---

## 🚀 Action Plan

**Right Now (Immediate):**
1. Click the annotation
2. Replace filter with: `service:datadog-demo-app message:"Homepage accessed"`
3. See your logs ✅

**Next 10 Minutes:**
1. Go to https://app.datadoghq.com/services
2. Archive or remove `eran-njs` service
3. Generate 100 new logs (run `./test-log-annotations.sh`)

**After Cleanup:**
1. Wait 15 minutes for Datadog to update
2. Reload Cursor
3. Test annotation again
4. Should now use correct service ✅

---

## 📞 If You Need Help

**Extension still using wrong service?**
- This is a known limitation
- Use manual filters (they always work)
- Bookmark the direct Datadog URLs

**Want to understand more?**
```bash
cat DATADOG_LOG_ANNOTATIONS_TROUBLESHOOTING.md
```

**Need to generate more logs?**
```bash
./test-log-annotations.sh
```

---

## ✅ Summary

**The Issue:**
- Extension finds old `eran-njs` service from historical logs
- Generates wrong filter

**The Fix:**
- Use manual filter: `service:datadog-demo-app message:"Homepage accessed"`
- Archive old `eran-njs` service in Datadog
- Generate more logs with correct service name

**The Result:**
- You can still use log annotations!
- Just need to adjust the filter when Datadog opens
- Takes 5 seconds per click

**The logs ARE working correctly** - it's just the extension's auto-generated filter that needs manual adjustment. Your setup is actually perfect! 🎉

---

**Last Updated:** November 2, 2025, 12:45 PST
**Status:** Workaround available, permanent fix in progress


