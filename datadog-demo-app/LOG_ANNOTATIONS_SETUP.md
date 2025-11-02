# 🎯 Datadog Extension Log Annotations Setup

## ❗ **Important Clarification**

The **Datadog Extension Log Annotations** feature you're referring to shows **visual annotations directly in your IDE** above logging code lines. These annotations display log volume and allow clicking to open Datadog Log Explorer.

## 🔧 **Current Status & Requirements**

### **What You Have:**
- ✅ Datadog extension installed
- ✅ Logging code in your application
- ✅ Logs being generated to files

### **What's Missing for Annotations:**
- ❌ Logs need to be shipped to Datadog (not just local files)
- ❌ Datadog extension needs proper API configuration
- ❌ Service needs to be connected to your Datadog account

---

## 🛠️ **Quick Setup for Demo**

### **Step 1: Configure Datadog Extension**

#### **In Cursor:**
1. **Click Datadog icon** in sidebar
2. **Click "Configure"** or settings gear
3. **Add your Datadog credentials:**
   - API Key: `[Your Datadog API Key]`
   - Application Key: `[Your Datadog App Key]`
   - Site: `datadoghq.com` (or your region)

### **Step 2: Verify Extension Configuration**

#### **Check Extension Status:**
1. **Open Command Palette**: `Cmd+Shift+P`
2. **Type**: "Datadog"
3. **Look for**: "Datadog: Show Service Summary"

---

## 🎬 **Demo Strategy (3 Options)**

### **Option A: If Annotations Are Working**

#### **Perfect Scenario:**
1. **Open** `src/app.js` (line 45)
2. **Look for gray text above logging lines** like:
   ```
   📊 12 logs in last hour
   logger.info('Homepage accessed', {
   ```
3. **Click the annotation** → Opens Datadog Log Explorer
4. **Show the filtered logs** in Datadog

### **Option B: If Annotations Aren't Visible Yet**

#### **Explain the Feature:**
> *"The Datadog extension automatically detects logging patterns and shows annotations above each line. In a fully configured environment, you'd see real-time metrics right here in the code."*

#### **Show the Code:**
1. **Point to logging lines** in `src/app.js:45`
2. **Explain**: "This line would show '25 logs in last hour'"
3. **Show multiple examples** in different files

### **Option C: Focus on the Integration**

#### **Demonstrate the Concept:**
1. **Show logging code** in multiple files
2. **Generate traffic** to create logs
3. **Show log volume** in terminal: `wc -l logs/combined.log`
4. **Explain**: "These numbers would appear as annotations in the IDE"

---

## 📍 **Key Files to Show**

### **1. Main App Logging (`src/app.js:45`)**
```javascript
logger.info('Homepage accessed', {
  dd: {
    trace_id: span?.context()?.toTraceId(),
    span_id: span?.context()?.toSpanId(),
  },
  user_agent: req.get('User-Agent'),
  ip_address: req.ip,
  endpoint: '/',
  log_volume_gauge: 1
});
```

### **2. User Operations (`src/routes/users.js:15`)**
```javascript
logger.info('Fetching all users', {
  operation: 'get_users',
  user_count: users.length,
  request_source: req.ip
});
```

### **3. Error Logging (`src/middleware/errorHandler.js:5`)**
```javascript
logger.error('Unhandled error occurred', {
  error_message: err.message,
  error_stack: err.stack,
  request_method: req.method,
  request_url: req.url
});
```

---

## 🎯 **Demo Script (3 Minutes)**

### **Minute 1: Show the Feature**
> *"The Datadog extension automatically detects logging patterns in your code and shows visual annotations above each logging line."*

**Actions:**
1. Open `src/app.js`
2. Navigate to line 45
3. Point to the logging code
4. Look for/explain annotations

### **Minute 2: Show Multiple Examples**
> *"Let me show you different types of logging patterns the extension detects."*

**Actions:**
1. Open `src/routes/users.js`
2. Show logging at lines 15, 55, 95
3. Open `src/middleware/errorHandler.js`
4. Show error logging

### **Minute 3: Generate Volume & Explain**
> *"Let me generate some traffic to show how the annotations update with real-time data."*

**Actions:**
```bash
for i in {1..10}; do curl -s http://localhost:3000/api/users > /dev/null; done
```

**Explain:**
> *"Each annotation shows log frequency and volume. Clicking opens Datadog Log Explorer filtered to that specific log line."*

---

## 🔧 **Backup Demo Plan**

### **If Annotations Don't Appear:**

#### **Show the Logs Instead:**
1. **Open** `logs/combined.log`
2. **Show the volume**: `wc -l logs/combined.log`
3. **Explain**: "These X logs would show as annotations in the IDE"

#### **Show Extension Panel:**
1. **Click Datadog icon** in sidebar
2. **Show any available metrics**
3. **Explain the integration**

#### **Focus on the Value:**
> *"In production, you'd see real-time metrics above each logging line, helping you understand which parts of your code generate the most logs."*

---

## 🎯 **Key Messages**

### **1. Automatic Detection**
> *"No configuration needed - the extension finds logging patterns automatically."*

### **2. Real-Time Metrics**
> *"See live log volume and frequency directly in your code."*

### **3. Direct Navigation**
> *"Click any annotation to jump to those logs in Datadog."*

### **4. Development Efficiency**
> *"Understand your logging patterns without leaving the IDE."*

---

## 📋 **Pre-Demo Checklist**

- [ ] Datadog extension configured with API keys
- [ ] Multiple files with logging code open in tabs
- [ ] Terminal ready for generating traffic
- [ ] Backup explanation ready if annotations don't show
- [ ] Log file available to show volume

**🚀 Your Log Annotations demo is ready!**
