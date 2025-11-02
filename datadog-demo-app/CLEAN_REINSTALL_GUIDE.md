# 🔄 Clean Reinstall Datadog Extension - Step by Step Guide

## ✅ Cache Cleared! Ready for Clean Install

All Datadog extension cache and data has been cleared:
- ✅ Extension global storage
- ✅ Cursor cache
- ✅ Cached data
- ✅ Code cache
- ✅ Settings reset with correct configuration

---

## 📋 Step-by-Step Reinstallation

### **Step 1: Close Cursor Completely**
```
Press: Cmd + Q
Wait: 5 seconds
```

### **Step 2: Reopen Cursor**
```
Click Cursor icon in Applications
Open: datadog-demo-app folder
```

### **Step 3: Install Datadog Extension**

**Method A: Via Extensions Panel**
```
1. Press: Cmd + Shift + X
2. Search: "Datadog"
3. Find: "Datadog" by Datadog
4. Click: Install
5. Wait for installation to complete
```

**Method B: Via Command Palette**
```
1. Press: Cmd + Shift + P
2. Type: "Extensions: Install Extensions"
3. Search: "Datadog"
4. Install: "Datadog" by Datadog
```

### **Step 4: Reload Cursor**
```
After installation completes:
Cmd + Shift + P → "Developer: Reload Window"
```

### **Step 5: Verify Configuration**

The extension should automatically pick up the configuration from `.vscode/settings.json`:

```json
{
  "datadog.site": "datadoghq.com",
  "datadog.apiKey": "be9f47b60fedd8042065bd3052eb546e",
  "datadog.service": "datadog-demo-app",
  "datadog.env": "demo",
  "datadog.logs.events.enabled": true
}
```

### **Step 6: Test Log Annotations**

1. Open: `src/app.js`
2. Go to: Line 50
3. Wait: 2-3 minutes for extension to query Datadog
4. Look for: Gray annotation text above `logger.info('Homepage accessed', {`

**Expected Result:**
```javascript
// X log events in past day  ← Should appear here
logger.info('Homepage accessed', {
```

---

## ⚠️ Important Notes

### **About the Service Filter Issue**

The extension may still show `service:(eran-njs)` because:
- The service name lookup is based on **Datadog's API responses**
- Even though we deleted the service, Datadog's API may cache service lists
- This can take **24-48 hours** to fully clear from Datadog's backend

### **Expected Behavior After Fresh Install**

**Scenario 1: Best Case** ✅
- Extension queries Datadog
- Only finds `datadog-demo-app`
- Uses correct service in filter
- Everything works!

**Scenario 2: Cache Still Exists** ⚠️
- Extension queries Datadog
- API still returns `eran-njs` in service list (cached)
- Extension picks wrong service again
- Need to use manual filter workaround

---

## 🔧 If Wrong Service Still Appears

### **Quick Workaround (5 seconds per click):**

When annotation opens Datadog, replace filter with:
```
service:datadog-demo-app message:"Homepage accessed"
```

### **Or Use Direct Links (Bookmark These):**

**All Logs:**
```
https://app.datadoghq.com/logs?query=service:datadog-demo-app
```

**Homepage Logs:**
```
https://app.datadoghq.com/logs?query=service:datadog-demo-app%20message:%22Homepage%20accessed%22
```

---

## 🎯 Alternative: Disable Log Annotations Initially

If you want to avoid the service filter issue while it clears:

**Edit `.vscode/settings.json`:**
```json
"datadog.logs.events.enabled": false,
```

Then **re-enable after 24-48 hours** when Datadog's API cache clears:
```json
"datadog.logs.events.enabled": true,
```

---

## ✅ Verification Checklist

After reinstalling, verify:

- [ ] Extension installed (check in Extensions panel)
- [ ] Cursor reloaded
- [ ] Configuration in `.vscode/settings.json` correct
- [ ] API key present in settings
- [ ] Service name: `datadog-demo-app`
- [ ] Waited 2-3 minutes for annotation to appear
- [ ] Annotation visible (even if service filter is wrong)
- [ ] Clicking annotation opens Datadog

---

## 🚀 Clean Start Configuration

Your `.vscode/settings.json` is now set to:

```json
{
  "datadog.site": "datadoghq.com",
  "datadog.apiKey": "be9f47b60fedd8042065bd3052eb546e",
  "datadog.logs.service.runtimeServiceName": "datadog-demo-app",
  "datadog.logs.service.enableServiceTracking": true,
  "datadog.logs.events.enabled": true,
  "datadog.logs.events.setup.autoRefresh": true,
  "datadog.service": "datadog-demo-app",
  "datadog.env": "demo"
}
```

This tells the extension:
- ✅ Use Datadog site: datadoghq.com
- ✅ Service name: datadog-demo-app
- ✅ Enable log annotations
- ✅ Auto-refresh enabled

---

## 📞 What to Expect

### **Timeline:**

**Immediately after install:**
- Extension downloads and activates
- Reads configuration from settings
- Starts background processes

**After 2-3 minutes:**
- Extension queries Datadog API for service list
- Scans your code for log patterns
- Matches patterns with Datadog logs
- Shows annotations above logger statements

**If service filter is wrong:**
- Extension found `eran-njs` in Datadog's cached service list
- Use manual filter workaround
- Or wait 24-48 hours for Datadog's cache to clear
- Then reinstall extension again

---

## 🎉 Summary

**Completed:**
- ✅ Uninstalled old extension
- ✅ Cleared ALL cache and data
- ✅ Reset configuration with correct values
- ✅ Ready for clean install

**Next Steps:**
1. Close Cursor (Cmd+Q)
2. Wait 5 seconds
3. Reopen Cursor
4. Install Datadog extension
5. Reload Cursor
6. Test annotations

**Your Datadog integration (logs, traces, metrics) continues working perfectly regardless of the extension!** 🎯

---

**Last Updated:** November 2, 2025
**Status:** Ready for clean reinstallation



