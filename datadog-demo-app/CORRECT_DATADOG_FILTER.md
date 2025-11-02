# 🎯 Correct Datadog Log Explorer Filter

## ❌ **Current Filter (Wrong)**
```
"Homepage accessed" ( service:(eran-njs) OR -service:* ) status:(info)
```

## ✅ **Correct Filter**
```
"Homepage accessed" service:datadog-demo-app status:info
```

---

## 🔧 **How to Fix the Filter**

### **Step 1: Clear Current Filter**
1. In Datadog Log Explorer, click the **X** next to each filter tag
2. Or click **Clear All** if available

### **Step 2: Add Correct Filters**

#### **Option A: Use Search Bar**
Type in the search bar:
```
"Homepage accessed" service:datadog-demo-app status:info
```

#### **Option B: Add Filters Manually**
1. **Add Service Filter:**
   - Click **"+ Add"** 
   - Select **"Service"**
   - Type: `datadog-demo-app`

2. **Add Status Filter:**
   - Click **"+ Add"**
   - Select **"Status"** 
   - Select: `info`

3. **Add Message Filter:**
   - In search bar, type: `"Homepage accessed"`

### **Step 3: Set Time Range**
- Set to **"Last 15 minutes"** or **"Last 1 hour"**

---

## 🎯 **Expected Results**

### **What You Should See:**
- **Service**: `datadog-demo-app`
- **Environment**: `demo`
- **Status**: `info`
- **Message**: Contains "Homepage accessed"
- **Source**: `nodejs`

### **Log Structure:**
```json
{
  "timestamp": "2025-11-02T07:30:00.000Z",
  "level": "info",
  "message": "Homepage accessed",
  "service": "datadog-demo-app",
  "dd": {
    "env": "demo",
    "service": "datadog-demo-app",
    "version": "1.0.0",
    "trace_id": "...",
    "span_id": "..."
  },
  "user_agent": "curl/7.64.1",
  "ip_address": "::1",
  "endpoint": "/"
}
```

---

## 🔍 **Alternative Searches**

### **For All App Logs:**
```
service:datadog-demo-app
```

### **For All Homepage Logs:**
```
service:datadog-demo-app "Homepage accessed"
```

### **For All API Logs:**
```
service:datadog-demo-app "Fetching"
```

### **For Error Logs:**
```
service:datadog-demo-app status:error
```

---

## 🎬 **For Your Demo**

### **Perfect Demo Filter:**
```
service:datadog-demo-app
```

**This will show ALL logs from your demo app, making it easy to:**
1. **Show log volume** across all endpoints
2. **Filter by specific messages** during the demo
3. **Demonstrate different log types** (info, error, etc.)

---

## 🚨 **If Still No Logs**

### **Check These:**

#### **1. Verify App is Running:**
```bash
curl http://localhost:3000/
```

#### **2. Check Local Logs:**
```bash
tail -f /Users/eran.rahmani/datadog-demo-app/logs/combined.log
```

#### **3. Verify Datadog Transport:**
Look for this message when app starts:
```
✅ Datadog transport configured
```

#### **4. Generate More Traffic:**
```bash
for i in {1..5}; do curl -s http://localhost:3000/ > /dev/null; done
```

---

## 🎯 **Summary**

**Change your Datadog filter from:**
- ❌ `service:(eran-njs)`

**To:**
- ✅ `service:datadog-demo-app`

**The logs should appear within 1-2 minutes! 🚀**
