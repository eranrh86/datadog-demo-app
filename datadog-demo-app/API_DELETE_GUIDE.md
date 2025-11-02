# 🗑️ Delete eran-njs Service Using Datadog API

## 📋 Quick Start

You now have a script to delete the `eran-njs` service using the Datadog API.

### **Step 1: Get Your Application Key**

The Datadog API requires both an **API Key** (you already have) and an **Application Key**.

**Get Application Key:**
1. Go to: https://app.datadoghq.com/organization-settings/application-keys
2. Click **"New Key"**
3. Name: `Service Management`
4. Click **"Create Key"**
5. **Copy the key** (you'll only see it once!)

### **Step 2: Run the Deletion Script**

```bash
cd /Users/eran.rahmani/datadog-demo-app

# Run with your Application Key
DD_APP_KEY='your-application-key-here' ./delete-eran-njs-service.sh
```

**Replace** `your-application-key-here` with the actual key you copied.

### **Step 3: Wait for Propagation**

After deletion:
- Wait **15-30 minutes** for Datadog to propagate changes
- Reload Cursor: `Cmd+Shift+P` → "Developer: Reload Window"
- Test the annotation again

---

## 🔧 What the Script Does

**Automated Steps:**
1. ✅ Verifies the service exists
2. 🗑️ Calls `DELETE /api/v2/services/definitions/eran-njs`
3. ✅ Confirms deletion
4. ✅ Verifies `datadog-demo-app` still exists

**API Endpoint Used:**
```bash
DELETE https://api.datadoghq.com/api/v2/services/definitions/eran-njs
Headers:
  - DD-API-KEY: be9f47b60fedd8042065bd3052eb546e
  - DD-APPLICATION-KEY: <your-app-key>
```

---

## 📊 Expected Output

### **Successful Deletion:**

```
╔════════════════════════════════════════════════════════════╗
║     🗑️  Delete eran-njs Service from Datadog              ║
╚════════════════════════════════════════════════════════════╝

📋 Configuration:
   API Key: be9f47b60fedd8042065...
   Site: datadoghq.com
   Service to delete: eran-njs

🔍 Step 1: Verifying service exists...
⚠️  Service 'eran-njs' found

🗑️  Step 2: Deleting service 'eran-njs'...
✅ Service 'eran-njs' deleted successfully!

╔════════════════════════════════════════════════════════════╗
║                    VERIFICATION                            ║
╚════════════════════════════════════════════════════════════╝

Waiting 5 seconds for changes to propagate...

🔍 Checking service catalog...
✅ Confirmed: eran-njs no longer in service catalog
✅ Checking datadog-demo-app exists...
✅ datadog-demo-app is active

╔════════════════════════════════════════════════════════════╗
║                    NEXT STEPS                              ║
╚════════════════════════════════════════════════════════════╝

1. Wait 15-30 minutes for Datadog to fully propagate changes
2. Verify in UI: https://app.datadoghq.com/services
3. Reload Cursor: Cmd+Shift+P → 'Developer: Reload Window'
4. Test log annotations in src/app.js line 50

🎉 Done!
```

### **Already Deleted:**

```
✅ Service 'eran-njs' not found in Datadog
   (Already deleted or never existed)
✅ datadog-demo-app exists
```

---

## 🔍 Manual Verification

After running the script, verify the deletion:

### **Check via API:**
```bash
# Should return 404
curl -s -o /dev/null -w "%{http_code}" \
  "https://api.datadoghq.com/api/v2/services/definitions/eran-njs" \
  -H "DD-API-KEY: be9f47b60fedd8042065bd3052eb546e" \
  -H "DD-APPLICATION-KEY: your-app-key"
```

**Expected:** `404` (Not Found) ✅

### **Check via UI:**
```
https://app.datadoghq.com/services
```
Search: `eran-njs`
**Expected:** No results ✅

### **Check Logs:**
```
https://app.datadoghq.com/logs?query=service:eran-njs
```
**Expected:** 0 logs (or only very old historical logs) ✅

---

## 🚨 Troubleshooting

### **Error: "Application Key Required"**

**Solution:** You need to create an Application Key first.

1. Go to: https://app.datadoghq.com/organization-settings/application-keys
2. Create a new key
3. Run the script with: `DD_APP_KEY='key' ./delete-eran-njs-service.sh`

### **Error: "403 Forbidden"**

**Cause:** Application Key doesn't have sufficient permissions.

**Solution:**
1. Go to: https://app.datadoghq.com/organization-settings/application-keys
2. Find your key
3. Ensure it has **"Service Catalog Management"** permission
4. Or create a new key with full permissions

### **Error: "404 Not Found"**

**Good news!** The service is already deleted or never existed. ✅

### **Cursor Extension Still Uses eran-njs**

**Cause:** Datadog's cache hasn't updated yet.

**Solution:**
1. Wait 30 minutes for propagation
2. Reload Cursor: `Cmd+Shift+P` → Reload Window
3. If still showing, use manual filter: `service:datadog-demo-app`

---

## 🔐 Security Notes

### **Application Key vs API Key**

| Key Type | Purpose | Permissions |
|----------|---------|-------------|
| **API Key** | Read/write data (logs, metrics) | Limited to data ingestion |
| **Application Key** | Manage resources (services, dashboards) | Can create/delete resources |

### **Best Practices**

1. **Create a dedicated key** for service management
2. **Name it clearly** (e.g., "Service Management - Temp")
3. **Delete it after use** if no longer needed
4. **Never commit keys** to git (already in .gitignore)

### **Revoking the Key**

After deletion, you can revoke the Application Key:
1. Go to: https://app.datadoghq.com/organization-settings/application-keys
2. Find your key
3. Click **"Revoke"**

---

## 📋 Alternative Methods

If you prefer not to use the API:

### **Method 1: Datadog UI (Easiest)**
```
1. Go to: https://app.datadoghq.com/services
2. Search: eran-njs
3. Click → Settings → Archive Service
```

### **Method 2: Stop Indexing Logs**
```
1. Go to: https://app.datadoghq.com/logs/pipelines
2. Create exclusion filter
3. Query: service:eran-njs
4. Logs will stop being indexed
```

### **Method 3: Wait for Natural Expiration**
- Logs expire after retention period (15-30 days)
- Service disappears when no recent logs
- No action needed, just wait

---

## ✅ Success Checklist

After running the script:

- [ ] Script completed successfully
- [ ] Verified: `eran-njs` returns 404 via API
- [ ] Verified: `eran-njs` not in service catalog UI
- [ ] Verified: `datadog-demo-app` still exists
- [ ] Waited 30 minutes for propagation
- [ ] Reloaded Cursor
- [ ] Tested log annotation (should use correct service)

---

## 🎯 Summary

**Files Created:**
- ✅ `delete-eran-njs-service.sh` - API deletion script
- ✅ `API_DELETE_GUIDE.md` - This guide

**To Delete the Service:**
```bash
# 1. Get Application Key from Datadog
# 2. Run the script:
DD_APP_KEY='your-app-key' ./delete-eran-njs-service.sh

# 3. Wait 30 minutes
# 4. Reload Cursor
# 5. Test annotations
```

**After Deletion:**
- ✅ `eran-njs` removed from Datadog
- ✅ Cursor extension will only see `datadog-demo-app`
- ✅ Annotations will use correct service filter
- ✅ No more manual filter adjustments needed!

---

**Last Updated:** November 2, 2025  
**Status:** Ready to execute  
**API Endpoint:** `DELETE /api/v2/services/definitions/eran-njs`


