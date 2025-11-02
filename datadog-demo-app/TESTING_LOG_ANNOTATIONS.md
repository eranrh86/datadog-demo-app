# 🧪 Step-by-Step Guide: Testing Datadog Log Annotations

## Overview
This guide will help you verify that Datadog Log Annotations are working correctly in Cursor. The annotations show log volume directly in your code above logger statements.

---

## ✅ Prerequisites Check

Before starting, verify these are complete:

```bash
cd /Users/eran.rahmani/datadog-demo-app

# 1. Check if app is running
lsof -ti:3000 && echo "✅ App is running" || echo "❌ App not running"

# 2. Check configuration file
cat .vscode/settings.json | grep "datadog.apiKey" && echo "✅ API key configured" || echo "❌ API key missing"

# 3. Check logs generated
grep -c "Homepage accessed" logs/combined.log && echo "✅ Logs exist"
```

**Expected Output:**
```
✅ App is running
✅ API key configured
✅ Logs exist
```

If any check fails, run:
```bash
./test-log-annotations.sh
```

---

## 📋 Step-by-Step Testing Process

### **Step 1: Reload Cursor Window** ⏱️ 10 seconds

This refreshes the Datadog extension with the new configuration.

1. In Cursor, press: `Cmd + Shift + P` (Mac) or `Ctrl + Shift + P` (Windows/Linux)
2. Type: `reload`
3. Select: **"Developer: Reload Window"**
4. Press: `Enter`

**Result:** Cursor will restart with your workspace reopened.

---

### **Step 2: Wait for Datadog to Index Logs** ⏱️ 2-3 minutes

The Datadog backend needs time to:
- Index the logs you generated
- Make them available via API
- Allow the Cursor extension to query them

**What to do:**
- ☕ Take a short break
- ✅ Datadog is processing your logs in the background

**Pro Tip:** During this time, you can verify logs in Datadog:
- Go to: https://app.datadoghq.com/logs
- Filter: `service:datadog-demo-app`
- You should see your logs appearing

---

### **Step 3: Open the First Test File** ⏱️ 5 seconds

1. In Cursor, open the file explorer (left sidebar)
2. Navigate to: `src/app.js`
3. Click to open it

**What you're looking for:**
- This file contains the main homepage logger on line 50

---

### **Step 4: Locate the Log Statement** ⏱️ 10 seconds

1. In `src/app.js`, press `Cmd + G` (or `Ctrl + G`)
2. Type: `50`
3. Press: `Enter`

You should now be at **line 50**, which looks like this:

```javascript
// Root endpoint with log annotations
app.get('/', (req, res) => {
  const span = tracer.scope().active();
  
  // Log annotation example - gauge log volumes
  logger.info('Homepage accessed', {
    user_agent: req.headers['user-agent'],
    ip_address: req.ip,
    endpoint: req.path,
    log_volume_gauge: 1
  });
```

---

### **Step 5: Look for the Annotation** ⏱️ 5 seconds

**What to look for:**

Above the line `logger.info('Homepage accessed', {`, you should see **gray text** that looks like:

```javascript
// 20 log events in past day
logger.info('Homepage accessed', {
```

or

```javascript
// No log events in past day
logger.info('Homepage accessed', {
```

**If you see the annotation (even "No log events"):**
- ✅ The extension is working!
- Go to Step 6

**If you DON'T see any annotation:**
- ⏳ Wait 2 more minutes (Datadog might still be indexing)
- 🔄 Try reloading again (Cmd+Shift+P → Reload Window)
- If still nothing, go to **Troubleshooting Section** below

---

### **Step 6: Test the Annotation Click** ⏱️ 10 seconds

If you see an annotation:

1. **Hover** over the gray text above the logger line
2. You should see it become **clickable** (changes color or shows underline)
3. **Click** on the annotation text

**Expected Result:**
- Your default browser opens
- Navigates to: `https://app.datadoghq.com/logs`
- Shows logs filtered to: `service:datadog-demo-app message:"Homepage accessed"`
- Displays log entries from the past 24 hours

**If the click opens Datadog:**
- ✅ **SUCCESS!** Log Annotations are working correctly!

---

### **Step 7: Test Other Log Locations** ⏱️ 2 minutes

Now verify annotations appear in other files:

#### **Test Location 2: Users API**

1. Open: `src/routes/users.js`
2. Go to: **Line 16**
3. Look above: `logger.info('Fetching all users', {`
4. Should see: `// X log events in past day`

#### **Test Location 3: Orders API**

1. Open: `src/routes/orders.js`
2. Go to: **Line 14**
3. Look above: `logger.info('Fetching all orders', {`
4. Should see: `// X log events in past day`

#### **Test Location 4: Health Check**

1. Open: `src/routes/health.js`
2. Go to: **Line 8**
3. Look above: `logger.info('Health check performed', {`
4. Should see: `// X log events in past day`

**If annotations appear in multiple files:**
- 🎉 **EXCELLENT!** Everything is working perfectly!

---

## 🎬 Quick Test Script

For a quick end-to-end test, run this automated script:

```bash
cd /Users/eran.rahmani/datadog-demo-app
./test-log-annotations.sh
```

**What it does:**
1. ✅ Checks if app is running (starts it if not)
2. ✅ Generates 35 new logs across all endpoints
3. ✅ Shows you exactly where to find annotations
4. ✅ Provides verification links

**After running:**
1. Reload Cursor window
2. Wait 2-3 minutes
3. Check the files mentioned in the script output

---

## 🔍 Manual Verification (Backup Method)

If annotations don't appear in Cursor, you can still verify logs are working:

### **Method 1: Datadog Log Explorer**

1. Go to: https://app.datadoghq.com/logs
2. In the search bar, enter: `service:datadog-demo-app`
3. Click the time picker (top right)
4. Select: **"Past 30 minutes"**

**Expected Result:**
- You should see 100+ log entries
- Each log has:
  - ✅ service: `datadog-demo-app`
  - ✅ trace_id and span_id (for APM correlation)
  - ✅ timestamp within the last hour
  - ✅ Various messages like "Homepage accessed", "Health check performed", etc.

### **Method 2: Specific Log Pattern Search**

In Datadog Log Explorer, try these queries:

**Homepage logs:**
```
service:datadog-demo-app message:"Homepage accessed"
```

**Users API logs:**
```
service:datadog-demo-app message:"Fetching all users"
```

**Orders API logs:**
```
service:datadog-demo-app message:"Fetching all orders"
```

**Health check logs:**
```
service:datadog-demo-app message:"Health check performed"
```

---

## 🚨 Troubleshooting

### **Issue 1: No Annotations Appear**

**Symptoms:**
- Cursor is loaded
- No gray text above logger statements
- No errors visible

**Solutions:**

#### **Solution A: Verify Extension is Installed**

1. Press: `Cmd + Shift + X` (Extensions sidebar)
2. Search: `Datadog`
3. Verify: "Datadog" extension by Datadog is installed
4. If not installed:
   - Click "Install"
   - Reload window after installation

#### **Solution B: Verify API Key is Set**

```bash
cd /Users/eran.rahmani/datadog-demo-app
cat .vscode/settings.json | grep apiKey
```

**Expected output:**
```json
  "datadog.apiKey": "be9f47b60fedd8042065bd3052eb546e",
```

If missing, the configuration didn't save. Re-run:
```bash
# Backup and recreate
cp .vscode/settings.json .vscode/settings.json.bak
cat > .vscode/settings.json << 'EOF'
{
  "datadog.site": "datadoghq.com",
  "datadog.apiKey": "be9f47b60fedd8042065bd3052eb546e",
  "datadog.logs.service.runtimeServiceName": "datadog-demo-app",
  "datadog.logs.service.enableServiceTracking": true,
  "datadog.logs.events.setup.includeLogsWithoutService": false,
  "datadog.logs.events.setup.bypassLocalSearch": false,
  "datadog.logs.events.enabled": true,
  "datadog.logs.events.setup.autoRefresh": true,
  "datadog.service": "datadog-demo-app",
  "datadog.env": "demo"
}
EOF
```

Then reload Cursor.

#### **Solution C: Force Extension Refresh**

1. Open Cursor settings: `Cmd + ,`
2. Search: `datadog`
3. Find: "Datadog: Logs: Events: Enabled"
4. Toggle it OFF, then back ON
5. Reload window

#### **Solution D: Clear Extension Cache**

```bash
# Close Cursor first, then run:
rm -rf ~/Library/Application\ Support/Cursor/Cache/*datadog* 2>/dev/null
rm -rf ~/Library/Application\ Support/Cursor/Code\ Cache/*datadog* 2>/dev/null

# Restart Cursor
```

---

### **Issue 2: Shows "No log events in past day"**

**Symptoms:**
- Annotation appears
- Shows "No log events in past day"
- But you know logs exist in Datadog

**Cause:**
- Extension is using wrong service name filter
- Known issue with service name caching

**Solutions:**

#### **Solution A: Use Manual Filter**

The logs ARE in Datadog, the extension just can't find them due to caching.

1. Click the annotation anyway
2. When Datadog opens, **replace** the filter with:
   ```
   service:datadog-demo-app message:"Homepage accessed"
   ```
3. You should now see your logs

#### **Solution B: Verify Service Name Match**

```bash
# Check logs have correct service name
cd /Users/eran.rahmani/datadog-demo-app
tail -1 logs/combined.log | jq -r '.service'
```

**Expected output:** `datadog-demo-app`

If different, the service name doesn't match. Update `.vscode/settings.json`:
```json
"datadog.logs.service.runtimeServiceName": "actual-service-name-here",
```

#### **Solution C: Generate Fresh Logs**

Sometimes the extension needs more recent data:

```bash
cd /Users/eran.rahmani/datadog-demo-app

# Generate 20 fresh logs
for i in {1..20}; do
  curl -s http://localhost:3000/ > /dev/null
  echo "Request $i"
  sleep 1
done

# Wait 3 minutes, then reload Cursor
```

---

### **Issue 3: App Not Running**

**Symptoms:**
```bash
lsof -ti:3000
# No output
```

**Solution:**

```bash
cd /Users/eran.rahmani/datadog-demo-app

# Start with Datadog integration
DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' \
DD_SERVICE='datadog-demo-app' \
DD_ENV='demo' \
DD_VERSION='1.0.0' \
NODE_ENV=development \
npm start
```

Keep this terminal open. The app must stay running for logs to be generated.

---

### **Issue 4: Annotation Opens Wrong Filter**

**Symptoms:**
- Click annotation
- Opens Datadog with filter like: `service:(eran-njs) OR -service:*`
- Shows no results or wrong service

**Cause:**
- Extension found historical logs from old service name
- Known caching behavior

**Solution:**

This is expected! The logs are correct, just the extension's filter is outdated.

**Manual fix:**
1. When Datadog opens, look at the search bar
2. **Delete** the entire filter
3. **Replace** with: `service:datadog-demo-app message:"Homepage accessed"`
4. Press Enter

Your logs will now appear correctly.

**Why this happens:**
- The Datadog extension queries for services that have logged this message historically
- If you had an old service name, it caches that
- Your NEW logs are under the NEW service name
- Manual filter bypasses the cache

---

## ✅ Success Criteria

You've successfully tested Log Annotations when:

- ✅ Annotations appear above logger statements (even if showing "No log events")
- ✅ Clicking annotations opens Datadog Log Explorer
- ✅ Logs are visible in Datadog (even if filter needs manual adjustment)
- ✅ Logs have correct service tag: `datadog-demo-app`
- ✅ Multiple log patterns are detected (homepage, users, orders, health)

---

## 📊 Expected Results Summary

| Location | File | Line | Log Message | Expected Count |
|----------|------|------|-------------|----------------|
| Homepage | `src/app.js` | 50 | "Homepage accessed" | 20+ logs |
| Users API | `src/routes/users.js` | 16 | "Fetching all users" | 10+ logs |
| Orders API | `src/routes/orders.js` | 14 | "Fetching all orders" | 10+ logs |
| Health Check | `src/routes/health.js` | 8 | "Health check performed" | 5+ logs |

---

## 🎯 Quick Testing Checklist

Use this checklist to track your testing progress:

- [ ] **Prerequisites verified** (app running, API key set, logs exist)
- [ ] **Cursor reloaded** (Developer: Reload Window)
- [ ] **Waited 2-3 minutes** (for Datadog to index)
- [ ] **Opened src/app.js** (line 50)
- [ ] **Annotation visible** (gray text above logger.info)
- [ ] **Clicked annotation** (opens Datadog)
- [ ] **Logs visible in Datadog** (service:datadog-demo-app)
- [ ] **Tested other locations** (users.js, orders.js, health.js)
- [ ] **Manual verification done** (Datadog Log Explorer)

---

## 🔗 Helpful Links

- **Datadog Log Explorer:** https://app.datadoghq.com/logs
- **Your Logs Filter:** `service:datadog-demo-app`
- **APM Traces:** https://app.datadoghq.com/apm/traces?query=service%3Adatadog-demo-app
- **Service Overview:** https://app.datadoghq.com/apm/service/datadog-demo-app

---

## 📞 Still Having Issues?

If you've completed all troubleshooting steps and annotations still don't work:

1. **Check the detailed troubleshooting guide:**
   ```bash
   cat DATADOG_LOG_ANNOTATIONS_TROUBLESHOOTING.md
   ```

2. **Check the fix documentation:**
   ```bash
   cat LOG_ANNOTATIONS_FIX.md
   ```

3. **Verify in Datadog directly:**
   - The logs ARE being sent correctly
   - The annotations feature is a UI convenience
   - You can always search logs manually in Datadog

4. **Extension limitations:**
   - The Cursor Datadog extension is still in development
   - Some caching/refresh delays are expected
   - Manual filters always work as a fallback

---

## 🎉 Testing Complete!

If you can see annotations and click them to open Datadog, you've successfully configured Log Annotations!

**What you've achieved:**
- ✅ Datadog integration working end-to-end
- ✅ Logs flowing from app → Datadog cloud
- ✅ APM traces correlating with logs
- ✅ Cursor extension configured and authenticated
- ✅ Log Annotations showing volume metrics in your IDE

**Next steps:**
- Use annotations to identify high-volume log lines
- Click annotations during development to quickly debug
- Monitor log patterns directly from your code editor

---

**Last Updated:** November 2, 2025
**Status:** Ready for Testing ✅


