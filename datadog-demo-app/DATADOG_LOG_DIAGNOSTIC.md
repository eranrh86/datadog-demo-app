# 🔍 Datadog Extension Log Diagnostic Guide

## How to Read Your 7230-Line Log

### Step 1: Search for Critical Errors

In the Datadog Output panel (Cmd+Shift+U → Datadog), search for these terms:

#### 🔴 Authentication Errors
```
Search: "401" or "unauthorized" or "invalid api key"
```
**If found:** API or Application key is invalid
**Fix:** Regenerate keys in Datadog

#### 🔴 Permission Errors
```
Search: "403" or "forbidden" or "permission"
```
**If found:** Application key lacks required permissions
**Fix:** Create new App Key with these scopes:
- `error_tracking_read`
- `code_analysis_read`
- `apm_service_catalog_read`

#### 🔴 Rate Limiting
```
Search: "429" or "rate limit" or "too many requests"
```
**If found:** Making too many API calls
**Fix:** Wait 10 minutes, then reload Cursor

#### 🔴 Service Not Found
```
Search: "service not found" or "no errors found for service"
```
**If found:** Service name mismatch
**Fix:** Verify service name exactly matches in:
- Datadog Error Tracking UI
- .vscode/settings.json ("datadog.service")
- Application logs (DD_SERVICE env var)

#### 🔴 Path Matching Issues
```
Search: "cannot match" or "no local file" or "path"
```
**If found:** Extension can't map Datadog paths to local files
**Fix:** Add path mapping (see below)

### Step 2: Check the Last 20 Lines

Scroll to the VERY BOTTOM of the log.

The last 20 lines show the most recent activity:

**GOOD SIGNS:**
- "Querying Error Tracking API..."
- "Found X errors"
- "Processing error: ..."
- "Matched error to file: ..."

**BAD SIGNS:**
- Repeated error messages
- "Failed to..." messages
- Empty/no recent activity

### Step 3: Look for Code Insights Activity

```
Search: "Code Insights" or "codeInsights" or "Error Tracking"
```

**If you see activity:** Extension is trying to work!
**If you see nothing:** Extension might not be activated

## Common Fixes

### Fix #1: Rate Limit (Most Common)

If you see "429" or "rate limit":

1. Wait 10 minutes (seriously, set a timer)
2. Reload Cursor: Cmd+Shift+P → "Developer: Reload Window"
3. Check Output panel again

### Fix #2: Missing Permissions

Your Application Key needs these scopes:

1. Go to: https://app.datadoghq.com/organization-settings/application-keys
2. Create new key with name: "Cursor Code Insights"
3. Enable scopes:
   - ✅ APM → error_tracking_read
   - ✅ Code Analysis → code_analysis_read
   - ✅ APM → apm_service_catalog_read
4. Copy the new key
5. Update `.vscode/settings.json`: `"datadog.applicationKey": "NEW_KEY"`
6. Reload Cursor

### Fix #3: Service Name Mismatch

Verify the service name is EXACTLY the same everywhere:

**In Datadog UI:**
1. Go to Error Tracking
2. Look at the service dropdown
3. Note the EXACT name (case-sensitive!)

**In settings.json:**
```json
"datadog.service": "datadog-demo-app"  ← Must match exactly!
```

**In running app:**
```bash
# Check what service name the app is using
curl http://localhost:30080/api/users/999
# Then check the error in Datadog - what service is it tagged with?
```

### Fix #4: Add Path Mapping

If extension can't match paths, add this to `.vscode/settings.json`:

```json
"datadog.codeInsights.sourceMaps": {
  "/app": "/Users/eran.rahmani/datadog-demo-app"
}
```

This maps Datadog's Docker path (`/app`) to your local path.

### Fix #5: Nuclear Option - Clean Reinstall

If nothing works:

```bash
# Stop Cursor completely
# Run this script:
rm -rf ~/Library/Application\ Support/Cursor/User/globalStorage/datadog.datadog-vscode
rm -rf ~/.vscode/extensions/datadog.*
```

1. Restart Cursor
2. Reinstall Datadog extension
3. Reload window
4. Wait 5 minutes

## What to Share With Me

To help you fix this, I need to know:

1. **Search for "error" or "fail":**
   - How many results?
   - Copy/paste 2-3 example lines

2. **Last 20 lines of the log:**
   - Scroll to bottom
   - Copy/paste the last 20 lines

3. **Search for "Code Insights":**
   - Do you find any results?
   - What do they say?

4. **Current status:**
   - Do you see red squiggles on line 48? (yes/no)
   - Do you see Datadog icon in status bar? (yes/no)
   - How long has it been since you reloaded Cursor?

Once you share these, I can pinpoint the exact issue!
