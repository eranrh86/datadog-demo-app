# 🗑️ ADMIN CLEANUP GUIDE - Remove eran-njs Service Completely

## System Status Report

### ✅ Already Correct (No cleanup needed)

#### Kubernetes/Minikube
- **Cluster:** `eran-k8` ✅
- **Namespace:** `datadog-demo` ✅
- **Deployment:** `datadog-demo-app` ✅
- **Service Name:** `datadog-demo-app` ✅ (Correct in ALL labels)
- **ConfigMap:** `datadog-demo-config` with `DD_SERVICE=datadog-demo-app` ✅
- **Environment:** All containers using correct service name ✅

#### Datadog Agent Configuration
- **Helm Release:** `datadog-agent` (version 3.141.0) ✅
- **Cluster Agent:** Correctly configured ✅
- **DaemonSet:** Correctly configured ✅
- **Tags:** All using `datadog-demo-app` ✅

#### Local Application
- **Service Name:** `datadog-demo-app` (hardcoded in dd-trace.init()) ✅
- **Environment Variables:** All set correctly ✅
- **Logger:** All logs tagged with `service:datadog-demo-app` ✅

### ❌ Needs Cleanup

#### Datadog Backend
- **Old Service:** `eran-njs` still in Datadog's service list
- **Historical Logs:** Some logs still tagged with `service:eran-njs`
- **Extension Suggestion:** Extension finds `eran-njs` when querying for log patterns

---

## Step-by-Step Cleanup

### Phase 1: Datadog UI (Manual) - RECOMMENDED

#### Option A: Delete the Service from Service Management (FASTEST)

1. **Login to Datadog**
   - URL: https://app.datadoghq.com
   - Go to: Catalog → Services

2. **Find the Service**
   - Search for: `eran-njs`
   - You should see it in the list

3. **Delete It**
   - Click on the service
   - Click the "..." menu (top right)
   - Select: "Delete Service"
   - Confirm the deletion

4. **Verify Deletion**
   - Search for `eran-njs` again
   - Should return no results

#### Option B: Archive Old Logs (Alternative)

If you can't delete the service (due to permissions), archive the old logs:

1. **Create a Log-Based Metric to Track Deletion**
   ```
   source:nodejs service:eran-njs
   ```

2. **Create an Archive**
   - Go to: Logs → Configuration → Archives
   - Click: "New Archive"
   - Set filter: `service:eran-njs`
   - Select: Archive all matching logs
   - Apply

3. **Wait 24 hours**
   - Datadog will reprocess service list
   - `eran-njs` will no longer appear in suggestions

---

### Phase 2: API Method (Automated) - FOR AUTOMATION

#### Check Current API Permissions

```bash
API_KEY="be9f47b60fedd8042065bd3052eb546e"
APP_KEY="1e9da0025c16055e0c07b1a9c3ff9a42e1db1263"

# Query current services
curl -s "https://api.datadoghq.com/api/v2/services" \
  -H "DD-API-KEY: $API_KEY" \
  -H "DD-APPLICATION-KEY: $APP_KEY" | jq .
```

#### Delete Service via API (If permissions allow)

```bash
# Delete the service
curl -X DELETE \
  "https://api.datadoghq.com/api/v2/services/eran-njs" \
  -H "DD-API-KEY: be9f47b60fedd8042065bd3052eb546e" \
  -H "DD-APPLICATION-KEY: 1e9da0025c16055e0c07b1a9c3ff9a42e1db1263"

# Verify deletion
curl "https://api.datadoghq.com/api/v2/services/eran-njs" \
  -H "DD-API-KEY: be9f47b60fedd8042065bd3052eb546e" \
  -H "DD-APPLICATION-KEY: 1e9da0025c16055e0c07b1a9c3ff9a42e1db1263"
```

#### Note on API Permissions

The current API key may need:
- `services_read` permission
- `services_write` permission
- Or requires using an Admin/Org API Key

**Recommendation:** Use Datadog UI method (Phase 1, Option A) - it's simpler

---

### Phase 3: Kubernetes Changes (NO CHANGES NEEDED)

Everything in Kubernetes is already correct:

```bash
# Verify all deployments use correct service name
kubectl get deployment -n datadog-demo -o yaml | grep -i "service"
# Result: tags.datadoghq.com/service: datadog-demo-app ✅

# Verify ConfigMap
kubectl get configmap datadog-demo-config -n datadog-demo -o yaml | grep DD_SERVICE
# Result: DD_SERVICE: datadog-demo-app ✅

# Verify annotations
kubectl get pods -n datadog-demo -o yaml | grep -i "service:"
# Result: service: datadog-demo-app ✅
```

**No Kubernetes cleanup needed!** Everything is using the correct service name.

---

### Phase 4: Datadog Agent (NO CHANGES NEEDED)

The Datadog agent is already correctly configured:

```bash
# Verify Helm values
helm get values datadog-agent -n datadog | grep -i "service"

# Verify DaemonSet configuration
kubectl get daemonset -n datadog -o yaml | grep -i "service" | head -10

# Verify logs are being tagged correctly
kubectl exec -it <pod-name> -n datadog -- cat /var/log/datadog/agent.log | grep eran-njs
```

**No agent cleanup needed!** Agent is already correctly configured.

---

## Verification Checklist

After cleanup, verify everything is working:

### ✅ Local Application
```bash
# Check logs are being sent with correct service
curl http://localhost:3000/
tail logs/combined.log | grep -i "Homepage accessed"
# Should show: "service":"datadog-demo-app" ✅
```

### ✅ Datadog UI
```
Filter: service:datadog-demo-app message:"Homepage accessed"
Result: Should show 15+ logs ✅
```

### ✅ VS Code Extension
1. Open Cursor
2. Go to `src/app.js` line 45
3. Hover over the log statement
4. Annotation should show logs from `datadog-demo-app` service ✅

### ✅ Query Check
```bash
# Verify eran-njs is gone
curl "https://api.datadoghq.com/api/v2/services/eran-njs" \
  -H "DD-API-KEY: be9f47b60fedd8042065bd3052eb546e" \
  -H "DD-APPLICATION-KEY: 1e9da0025c16055e0c07b1a9c3ff9a42e1db1263"
# Should return 404 or empty result
```

---

## Summary

### What to Do
1. **Go to:** Datadog → Catalog → Services
2. **Find:** `eran-njs`
3. **Click:** The service
4. **Delete:** Use the "..." menu → "Delete Service"
5. **Verify:** Annotation in Cursor shows correct service

### What NOT to Do
- ❌ Don't modify Kubernetes (already correct)
- ❌ Don't modify Datadog agent (already correct)
- ❌ Don't modify local application (already correct)
- ❌ Don't restart anything (not needed)

### Time Required
- **UI Method:** 2 minutes
- **API Method:** 5 minutes (if permissions allow)
- **Archive Method:** 24 hours for Datadog reprocessing

### Result After Cleanup
✅ Extension will suggest correct service name  
✅ Annotation will show 15+ logs immediately  
✅ No more "No log events in the past day" error  
✅ Log filtering will work perfectly

---

## FAQ

**Q: Will deleting the service affect existing logs?**
A: No. Deleting the service definition only removes it from the service list. Historical logs tagged with `service:eran-njs` will remain searchable.

**Q: Should I also delete historical logs?**
A: No, it's not necessary. Only the service definition needs to be deleted.

**Q: How long until the extension shows the correct service?**
A: Immediately after you reload Cursor (⌘⇧P → "Reload Window").

**Q: Will this affect any other applications?**
A: No. `eran-njs` was only used by the old application. The new app uses `datadog-demo-app`.

**Q: Do I need to restart anything?**
A: Yes, reload Cursor (⌘⇧P → "Reload Window") to see the changes.

---

## Support

If you encounter issues:

1. **Service not found in UI?**
   - Try searching: "eran"
   - Try: Logs → search `service:eran-njs`

2. **API permission denied?**
   - Check your API key has `services_write` permission
   - Or use a different/admin API key

3. **Still showing old service after deletion?**
   - Wait 10 minutes for Datadog cache to refresh
   - Reload Cursor: ⌘⇧P → "Reload Window"
   - Clear Cursor cache: ⌘⇧P → "Developer: Clear Cache"

4. **Extension still not showing logs?**
   - Run: `for i in {1..10}; do curl http://localhost:3000/; done`
   - Wait 5 seconds
   - Reload Cursor extension

---

**Last Updated:** November 2, 2025  
**Status:** Ready for cleanup  
**Estimated Time:** 2-5 minutes  
**Result:** Complete resolution of extension issue  

EOF

cat /Users/eran.rahmani/datadog-demo-app/ADMIN_CLEANUP_GUIDE.md





