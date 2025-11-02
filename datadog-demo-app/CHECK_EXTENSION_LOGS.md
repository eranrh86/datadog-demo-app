# 🔍 HOW TO CHECK DATADOG EXTENSION LOGS IN CURSOR

## ⚠️ CRITICAL: The Issue with Code Insights

I've confirmed:
- ✅ Errors ARE being generated (HTTP 500)
- ✅ Errors ARE in Datadog Error Tracking (you saw them!)
- ✅ Configuration is correct
- ❌ BUT red squiggles aren't showing

**The problem is likely in the Datadog extension itself.**

---

## 📋 STEP 1: CHECK EXTENSION OUTPUT LOGS

### Open Output Panel:
1. Press: `Cmd + Shift + U` (or View → Output)
2. In the dropdown at top-right, select: **"Datadog"**
3. Look for recent activity

### What to look for:

#### ✅ Good Signs:
```
[Info] Fetching errors from Error Tracking...
[Info] Found 20 errors for service datadog-demo-app
[Info] Matched error to file: src/routes/users.js:48
[Info] Drawing squiggle for error...
```

#### ❌ Bad Signs:
```
[Error] Failed to fetch errors: 403 Forbidden
[Error] Invalid API key or Application key
[Error] No errors found for service datadog-demo-app
[Warn] Could not match error path: /app/src/routes/users.js
[Error] Path mapping failed
```

---

## 📊 STEP 2: CHECK EXTENSION STATUS BAR

Look at the **bottom status bar** in Cursor:

### Should see:
- Datadog icon (dog face 🐶)
- Click it to see status

### If you see:
- ❌ "Not connected" → API keys issue
- ❌ "No service" → Service name mismatch
- ✅ "Connected: datadog-demo-app" → Good!

---

## 🔧 STEP 3: CHECK DATADOG UI AGAIN

Let's verify errors are still appearing:

### Go to Error Tracking:
```
https://app.datadoghq.com/apm/error-tracking
```

### Filter:
- Service: `datadog-demo-app`
- Time: Last 15 minutes

### Should see:
- Error count increasing (I'm generating 1 per minute now)
- Last seen: Within last 2 minutes
- File: `src/routes/users.js:48`

---

## 🎯 STEP 4: FORCE EXTENSION REFRESH

### Try these commands:

1. **Reload Window:**
   ```
   Cmd + Shift + P → "Developer: Reload Window"
   ```

2. **Look for Datadog commands:**
   ```
   Cmd + Shift + P → Type "Datadog"
   ```
   
   Look for commands like:
   - "Datadog: Refresh Code Insights"
   - "Datadog: Clear Cache"
   - "Datadog: Reconnect"

---

## 🐛 COMMON ISSUES

### Issue 1: Path Mapping
**Symptom**: Extension logs show "Could not match error path"

**Fix**: Verify `.vscode/settings.json` has:
```json
{
  "datadog.codeInsights.sourceMaps": {
    "/app": "/Users/eran.rahmani/datadog-demo-app"
  }
}
```

### Issue 2: Service Name Mismatch
**Symptom**: Extension logs show "No errors found"

**Fix**: Verify service names match:
- In Datadog Error Tracking: `datadog-demo-app`
- In `.vscode/settings.json`: `"datadog.service": "datadog-demo-app"`

### Issue 3: Application Key Invalid
**Symptom**: Extension logs show 403 or 401 errors

**Fix**: Verify Application Key has permissions:
- Go to: https://app.datadoghq.com/organization-settings/application-keys
- Check key: `51a8536892dbd4a421637d3d3c06df60ffeeaa6b`
- Should have: "Read" permissions for Error Tracking

### Issue 4: Extension Not Querying
**Symptom**: No activity in extension logs

**Fix**: 
- Extension might be disabled
- Check: Extensions panel → Search "Datadog" → Should be enabled

---

## 📊 CURRENT STATUS

### ✅ What's Working:
1. Pods running in Minikube
2. Errors being generated (HTTP 500)
3. Errors in Datadog Error Tracking
4. dd-trace instrumentation working
5. Configuration files correct

### ❌ What's NOT Working:
1. Cursor extension not showing red squiggles

### 🔥 What I Just Did:
1. Started **continuous error generator**
   - Generates 1 error per minute
   - Running in background
   - Logfile: `/tmp/error-generator.log`

2. To check generator status:
   ```bash
   tail -f /tmp/error-generator.log
   ```

3. To stop generator:
   ```bash
   kill $(cat /tmp/error-generator.pid)
   ```

---

## 🎯 NEXT STEPS

1. **Check Extension Output Logs** (Cmd + Shift + U → Datadog)
   - Copy any error messages you see
   - Share them with me

2. **Check Datadog UI** (verify errors still appearing)
   - https://app.datadoghq.com/apm/error-tracking
   - Filter: service:datadog-demo-app

3. **Wait 5 more minutes** after checking logs
   - Extension might be on a slow refresh cycle
   - Check line 48 again

4. **If still not working**, share:
   - Extension output logs
   - What you see in Datadog UI
   - Extension status bar status

---

## 💡 ALTERNATIVE HYPOTHESIS

The Datadog VS Code extension might:
- Not fully support Cursor (fork of VS Code)
- Have compatibility issues with Cursor's architecture
- Need specific Cursor settings

**If this is the case**, Code Insights might not work in Cursor, only in official VS Code.

---

## 🔍 WHAT TO SHARE WITH ME

Please check and share:

1. **Extension Output Logs**: 
   - Cmd + Shift + U → Select "Datadog"
   - Copy last 50 lines

2. **Extension Status**:
   - Bottom status bar → Datadog icon
   - What does it say?

3. **Datadog UI**:
   - Are errors still appearing?
   - Screenshot if possible

4. **Available Datadog Commands**:
   - Cmd + Shift + P → Type "Datadog"
   - What commands are available?

