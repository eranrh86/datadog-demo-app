# 🔑 Datadog API Key Setup for Log Annotations

## 🎯 **The Issue**
Your Datadog extension is working (you can see the annotation "No log events in the past day"), but logs aren't reaching Datadog - they're only going to local files.

## 🔧 **Quick Fix**

### **Step 1: Get Your Datadog API Key**

#### **Option A: From Datadog UI**
1. Go to [Datadog](https://app.datadoghq.com/)
2. Navigate to **Organization Settings** → **API Keys**
3. Copy an existing API key or create a new one

#### **Option B: From Your Existing Setup**
Since you already have Datadog working with your minikube cluster, you likely have the API key in:
- Kubernetes secrets
- Helm values
- Environment variables

### **Step 2: Set the API Key**

#### **Option A: Export Environment Variable**
```bash
export DD_API_KEY='your-datadog-api-key-here'
```

#### **Option B: Run with API Key**
```bash
DD_API_KEY='your-key' ./start-with-datadog.sh
```

### **Step 3: Restart the Application**

#### **Stop Current App:**
```bash
lsof -ti:3000 | xargs kill -9
```

#### **Start with Datadog Integration:**
```bash
./start-with-datadog.sh
```

---

## 🎬 **For Your Demo Tomorrow**

### **Quick Demo Setup (2 minutes):**

#### **1. Set API Key:**
```bash
export DD_API_KEY='your-actual-api-key'
```

#### **2. Start App:**
```bash
./start-with-datadog.sh
```

#### **3. Generate Traffic:**
```bash
# Generate some logs
for i in {1..5}; do curl -s http://localhost:3000/ > /dev/null; done
for i in {1..3}; do curl -s http://localhost:3000/api/users > /dev/null; done
```

#### **4. Check Datadog:**
- Wait 1-2 minutes for logs to appear
- Refresh your Datadog Log Explorer
- Look for service: `datadog-demo-app`

#### **5. Show Annotations:**
- Go back to Cursor
- Look at line 45 in `src/app.js`
- The annotation should now show log counts instead of "No log events"

---

## 🔍 **Verification**

### **Check if Logs are Being Sent:**
When you start the app, you should see:
```
✅ Datadog transport configured
🚀 Starting Datadog Demo App with Datadog Integration...
✅ Application is running on http://localhost:3000
✅ Logs are being sent to Datadog
```

### **If You See:**
```
⚠️ DD_API_KEY not set - logs will only go to files
```
Then the API key isn't configured properly.

---

## 🎯 **Expected Result**

### **Before Fix:**
```javascript
// No log events in the past day ← Gray text in IDE
logger.info('Homepage accessed', {
```

### **After Fix:**
```javascript
// 🔥 15 logs in last hour ← Gray text in IDE
logger.info('Homepage accessed', {
```

### **When You Click the Annotation:**
- Opens Datadog Log Explorer
- Shows filtered logs from that specific line
- Displays log volume over time

---

## 🚨 **Troubleshooting**

### **If Annotations Still Show "No log events":**

#### **1. Check Datadog Log Explorer:**
- Search for: `service:datadog-demo-app`
- Verify logs are appearing

#### **2. Check Service Name:**
- Make sure the service name in Cursor matches: `datadog-demo-app`

#### **3. Wait Time:**
- Logs can take 1-2 minutes to appear in Datadog
- Annotations update every few minutes

#### **4. Refresh Extension:**
- In Cursor: `Cmd+Shift+P` → "Developer: Reload Window"

---

## 🎬 **Demo Backup Plan**

### **If Annotations Don't Update in Time:**

#### **Show the Integration:**
1. **Point to the code:** "This is where the annotation will appear"
2. **Show Datadog logs:** Open Log Explorer with your logs
3. **Explain the feature:** "In production, you'd see real-time metrics here"

#### **Show the Value:**
> *"The Datadog extension automatically detects logging patterns and shows volume metrics directly in your code. This helps developers understand which parts of their application generate the most logs."*

---

## 🚀 **Your Demo is Ready!**

1. **Set DD_API_KEY** ✅
2. **Run ./start-with-datadog.sh** ✅
3. **Generate traffic** ✅
4. **Show annotations in Cursor** ✅
5. **Click to open Datadog** ✅

**The log annotations will now show real data! 🎯**
