# 🔍 Code Insights Setup Guide

## ✅ Code Insights Enabled!

I've configured the Datadog extension to show Code Insights directly in your IDE.

---

## 🎯 What Code Insights Provides

### **1. Runtime Errors** 🔴 (Error Tracking)
- Shows errors from production/staging
- Displays error frequency and stack traces
- Highlights problematic code lines
- **Color:** Red squiggles

### **2. Code & Library Vulnerabilities** 🟡 (Code Security)
- Detects security vulnerabilities in your code
- Flags vulnerable dependencies
- Shows CVE details and severity
- **Color:** Yellow/orange squiggles

### **3. Flaky Tests** 🔵 (Test Optimization)
- Identifies unreliable tests
- Shows flakiness percentage
- Helps improve test stability
- **Color:** Blue squiggles

---

## ⚙️ Configuration Applied

**File:** `.vscode/settings.json`

```json
{
  "datadog.site": "datadoghq.com",
  "datadog.apiKey": "be9f47b60fedd8042065bd3052eb546e",
  "datadog.applicationKey": "111598aa16769f02d37a20e99b645031baa2e5a1",
  "datadog.service": "datadog-demo-app",
  "datadog.env": "demo",
  
  // Code Insights Configuration
  "datadog.codeInsights.enabled": true,
  "datadog.codeInsights.errorTracking.enabled": true,
  "datadog.codeInsights.codeSecurity.enabled": true,
  "datadog.codeInsights.testOptimization.enabled": true
}
```

---

## 🚀 Next Steps

### **Step 1: Reload Cursor**
```
Cmd + Shift + P → "Developer: Reload Window"
```

### **Step 2: Wait for Analysis** (2-5 minutes)
The extension needs to:
- Query Datadog Error Tracking API
- Scan for code vulnerabilities
- Analyze test results
- Match errors to your code

### **Step 3: Look for Squiggles**
Open files in your codebase and look for colored underlines:
- 🔴 **Red** = Runtime errors
- 🟡 **Yellow** = Security vulnerabilities
- 🔵 **Blue** = Flaky tests

### **Step 4: Hover for Details**
Hover over any squiggle to see:
- Error details
- Stack trace
- Frequency
- Link to Datadog

---

## 📍 Where to See Code Insights

### **Error Tracking** 🔴

**Files with errors:**
- `src/app.js` - Line 98 (intentional error endpoint)
- `src/routes/users.js` - Line 48 (null reference error)

**Generate more errors:**
```bash
# Trigger error endpoint
curl http://localhost:3000/api/users/999
curl http://localhost:3000/error/runtime
```

**View in Datadog:**
```
https://app.datadoghq.com/apm/error-tracking?query=service:datadog-demo-app
```

---

### **Code Security** 🟡

**Check for vulnerabilities:**
```bash
npm audit
```

The extension will:
- Scan `package.json` dependencies
- Check for known CVEs
- Highlight vulnerable packages
- Show in `package.json` and import statements

**View in Datadog:**
```
https://app.datadoghq.com/security/csm
```

---

### **Test Optimization** 🔵

**Run tests:**
```bash
npm test
```

If you have flaky tests, the extension will:
- Highlight test functions
- Show flakiness percentage
- Link to test results in Datadog

**View in Datadog:**
```
https://app.datadoghq.com/ci/test-services
```

---

## 🔍 How to Use Code Insights

### **Example: Runtime Error**

When you see a red squiggle:

**Step 1: Hover over the line**
```
Shows:
- Error message: "Cannot read properties of null"
- Occurrences: 15 times in last 24 hours
- Last seen: 2 minutes ago
- Stack trace preview
```

**Step 2: Click "View in Datadog"**
- Opens Error Tracking in Datadog
- Shows full error details
- Displays affected users
- Shows error trends

**Step 3: Fix the issue**
- Update your code
- Deploy
- Squiggle disappears when error stops

---

### **Example: Security Vulnerability**

When you see a yellow squiggle on a package:

**Step 1: Hover over the import/require**
```
Shows:
- CVE-ID: CVE-2023-XXXXX
- Severity: High
- Affected versions: < 2.0.0
- Fixed in: 2.0.1
```

**Step 2: Click "View Details"**
- Opens vulnerability details
- Shows remediation steps
- Links to CVE database

**Step 3: Update the package**
```bash
npm update package-name
```

---

## 🛠️ Configuration Options

### **Enable/Disable Features**

**Disable Error Tracking:**
```json
"datadog.codeInsights.errorTracking.enabled": false
```

**Disable Code Security:**
```json
"datadog.codeInsights.codeSecurity.enabled": false
```

**Disable Test Optimization:**
```json
"datadog.codeInsights.testOptimization.enabled": false
```

**Disable All Code Insights:**
```json
"datadog.codeInsights.enabled": false
```

---

### **Advanced Settings**

**Error Threshold (minimum occurrences to show):**
```json
"datadog.codeInsights.errorTracking.minOccurrences": 5
```

**Time Range for errors:**
```json
"datadog.codeInsights.errorTracking.timeRange": "24h"
```

**Severity Filter:**
```json
"datadog.codeInsights.codeSecurity.minSeverity": "medium"
```

---

## ✅ Verification Steps

### **1. Check Extension Status**

Look at the bottom status bar:
- Should show Datadog icon
- Should say "Analyzing..." or "Ready"

### **2. Check Output Panel**

```
Cmd + Shift + U (Output)
Select: "Datadog"
```

Look for:
- "Code Insights enabled"
- "Querying Error Tracking..."
- "Found X errors"
- "Scanning for vulnerabilities..."

### **3. Generate Test Errors**

**Trigger errors to see squiggles:**
```bash
# Generate 5 errors
for i in {1..5}; do
  curl http://localhost:3000/api/users/999
  sleep 1
done
```

**Wait 2-3 minutes**, then:
- Open `src/routes/users.js`
- Look at line 48 (the error line)
- Should see red squiggle

---

## 📊 Expected Results

### **After Setup:**

**src/routes/users.js** (line 48):
```javascript
// Red squiggle appears here after errors are tracked
const profile = user.profile.firstName;  // ← Error: Cannot read 'profile' of null
```

**package.json**:
```json
{
  "dependencies": {
    "vulnerable-package": "1.0.0"  // ← Yellow squiggle if vulnerable
  }
}
```

**tests/users.test.js**:
```javascript
it('should fetch user', async () => {  // ← Blue squiggle if flaky
  // test code
});
```

---

## 🚨 Troubleshooting

### **No Squiggles Appearing**

**Check 1: Application Key Set?**
```bash
cat .vscode/settings.json | grep applicationKey
```
Should show your app key.

**Check 2: Service Name Correct?**
```json
"datadog.service": "datadog-demo-app"  // Must match your service
```

**Check 3: Errors Exist in Datadog?**
```
https://app.datadoghq.com/apm/error-tracking?query=service:datadog-demo-app
```
Must have errors tracked.

**Check 4: Extension Running?**
```
Cmd + Shift + X
Search: "Datadog"
Should show: "Enabled"
```

**Check 5: Reload Cursor**
```
Cmd + Shift + P → "Developer: Reload Window"
```

---

### **Only Some Features Working**

**Error Tracking requires:**
- ✅ Errors in Datadog APM
- ✅ Application Key
- ✅ Service name match
- ✅ Error Tracking enabled in Datadog

**Code Security requires:**
- ✅ Dependencies in package.json
- ✅ Known vulnerabilities
- ✅ Code Security enabled in Datadog org

**Test Optimization requires:**
- ✅ CI/CD tests running
- ✅ Test results sent to Datadog
- ✅ CI Visibility configured

---

## 🎯 Demo Script

Want to see Code Insights in action?

### **1. Generate Errors**
```bash
# Create 10 errors
for i in {1..10}; do
  curl http://localhost:3000/api/users/999
  sleep 1
done
```

### **2. Wait 3 Minutes**
Extension queries Datadog every few minutes

### **3. Open Error File**
```
src/routes/users.js
```

### **4. Look at Line 48**
Should see red squiggle

### **5. Hover Over It**
Shows error details from Datadog

### **6. Click "View in Datadog"**
Opens Error Tracking in browser

---

## 📚 Additional Resources

**Error Tracking:**
```
https://docs.datadoghq.com/tracing/error_tracking/
```

**Code Security:**
```
https://docs.datadoghq.com/security/application_security/
```

**Test Optimization:**
```
https://docs.datadoghq.com/tests/
```

**VS Code Extension:**
```
https://docs.datadoghq.com/developers/ide_plugins/vscode/
```

---

## 🎉 Summary

**Enabled:**
- ✅ Code Insights
- ✅ Error Tracking integration
- ✅ Code Security scanning
- ✅ Test Optimization

**Next:**
1. Reload Cursor
2. Wait 2-5 minutes
3. Look for colored squiggles
4. Hover for details
5. Click to view in Datadog

**Your code now has live insights from Datadog!** 🚀

---

**Last Updated:** November 2, 2025
**Status:** Configured and ready

