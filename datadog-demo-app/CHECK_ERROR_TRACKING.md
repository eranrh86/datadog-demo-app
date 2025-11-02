# 🔍 HOW TO CHECK IF ERRORS ARE IN DATADOG ERROR TRACKING

## ❌ THE PROBLEM

You don't see errors in Datadog Error Tracking, which means Code Insights can't show red squiggles.

## 🎯 STEP 1: CHECK DATADOG UI FIRST

### Go to Datadog Error Tracking:
```
https://app.datadoghq.com/apm/error-tracking
```

### Filter by your service:
1. Click "Service" filter
2. Select: `datadog-demo-app`
3. Set time range to: **Last 1 Hour**

### What to look for:
- ✅ **If you see errors**: Great! Code Insights should work
- ❌ **If you see NO errors**: The problem is errors aren't reaching Datadog

---

## 🔧 STEP 2: IF NO ERRORS IN DATADOG

The issue is that **dd-trace** isn't configured to send errors to Error Tracking.

### The Fix I Just Made:

I updated `src/middleware/errorHandler.js` to:
1. Get the active trace span
2. Set error tags on the span
3. This tells Datadog APM to report the error to Error Tracking

### What needs to happen:

1. **Restart the pods** (to load the new code)
2. **Generate new errors** (after restart)
3. **Wait 2-3 minutes** for errors to appear in Datadog
4. **Check Datadog UI** again

---

## 🚀 STEP 3: RESTART & TEST

### Option A: Restart Pods (Recommended)
```bash
kubectl rollout restart deployment/datadog-demo-app -n datadog-demo
kubectl rollout status deployment/datadog-demo-app -n datadog-demo
```

### Option B: Delete Pods (Force restart)
```bash
kubectl delete pods -n datadog-demo -l app=datadog-demo-app
kubectl wait --for=condition=ready pod -l app=datadog-demo-app -n datadog-demo --timeout=60s
```

### Generate Errors:
```bash
POD_NAME=$(kubectl get pods -n datadog-demo -l app=datadog-demo-app -o jsonpath='{.items[0].metadata.name}')

for i in {1..10}; do
  kubectl exec -n datadog-demo $POD_NAME -- wget -q -O- http://localhost:3000/api/users/999
  echo "Error $i generated"
  sleep 1
done
```

---

## 📊 STEP 4: VERIFY IN DATADOG

### After 2-3 minutes, check:

1. **Error Tracking**:
   - URL: https://app.datadoghq.com/apm/error-tracking
   - Filter: `service:datadog-demo-app`
   - Should see: `TypeError: Cannot read properties of null`

2. **APM Traces**:
   - URL: https://app.datadoghq.com/apm/traces
   - Filter: `service:datadog-demo-app status:error`
   - Should see: Red error traces

---

## ✅ STEP 5: THEN CHECK CODE INSIGHTS

### Only AFTER you see errors in Datadog:

1. **Reload Cursor**:
   ```
   Cmd + Shift + P → "Developer: Reload Window"
   ```

2. **Wait 5 minutes** (extension queries Datadog every few minutes)

3. **Check line 48** in `src/routes/users.js`:
   - Should see: **RED WAVY UNDERLINE**
   - Hover: Should show error details

---

## 🐛 TROUBLESHOOTING

### If STILL no errors in Datadog after restart:

1. **Check APM is working**:
   ```
   https://app.datadoghq.com/apm/services
   ```
   - Should see `datadog-demo-app` service
   - Should see recent traces

2. **Check pod logs for dd-trace**:
   ```bash
   kubectl logs -n datadog-demo deployment/datadog-demo-app | grep -i "datadog\|trace\|error"
   ```

3. **Verify DD_AGENT_HOST**:
   ```bash
   kubectl exec -n datadog-demo deployment/datadog-demo-app -- env | grep DD_
   ```

---

## 📝 SUMMARY

**The root cause**: dd-trace wasn't tagging spans with error information, so Datadog APM didn't know to send errors to Error Tracking.

**The fix**: Updated error handler to set error tags on spans.

**Next steps**:
1. Restart pods
2. Generate errors
3. Wait 2-3 minutes
4. Check Datadog Error Tracking UI
5. If errors appear → Code Insights will work
6. If no errors → Check APM configuration

