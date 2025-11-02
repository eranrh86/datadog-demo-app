# 🎯 Datadog Extension Log Annotations Demo

## 📋 **What This Feature Does**
The Datadog VS Code Extension automatically detects logging patterns in your code and shows **visual annotations** above the code lines. These annotations display:
- **Log volume** (how many times this log line executed)
- **Click to open** Log Explorer in Datadog
- **Real-time metrics** about log frequency

---

## 🔧 **Prerequisites for Log Annotations to Work**

### **1. Datadog Extension Must Be Configured**
- ✅ Extension installed (you have this)
- ✅ API keys configured
- ✅ Service connected to Datadog

### **2. Logs Must Be Flowing to Datadog**
Your current setup sends logs to files, but for the extension annotations to work, logs need to reach Datadog. Let me fix this:

---

## 🛠️ **Step 1: Configure Datadog Log Shipping**

### **Update Logger Configuration**
Let me modify your logger to send logs to Datadog:

```javascript
// Add to src/utils/logger.js
const winston = require('winston');

// Datadog transport (if available)
let transports = [
  new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }),
  new winston.transports.File({
    filename: 'logs/combined.log',
    maxsize: 5242880,
    maxFiles: 5
  })
];

// Add Datadog transport if API key is available
if (process.env.DD_API_KEY) {
  const DatadogWinston = require('datadog-winston');
  transports.push(new DatadogWinston({
    apiKey: process.env.DD_API_KEY,
    hostname: 'datadog-demo-app',
    service: 'datadog-demo-app',
    ddsource: 'nodejs',
    ddtags: 'env:demo,version:1.0.0'
  }));
}
```

---

## 🎬 **Step 2: Demo Script for Log Annotations**

### **Part A: Show the Code with Logging (1 minute)**

#### **Action 1: Open Main App File**
```
1. Press Cmd+P
2. Type: "app.js"
3. Press Enter
```

#### **Action 2: Navigate to Logging Code**
```
1. Press Cmd+G
2. Type: "45"
3. Press Enter to go to line 45
```

#### **Action 3: Point Out the Logging Code**
**Show this code and say:**
> *"Here's a typical logging statement in our application. The Datadog extension will automatically detect this pattern and show annotations above it."*

```javascript
// Line 45
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

### **Part B: Show More Logging Examples (1 minute)**

#### **Action 4: Open User Routes**
```
1. Press Cmd+P
2. Type: "users.js"
3. Press Enter
```

#### **Action 5: Navigate to User Logging**
```
1. Press Cmd+G
2. Type: "15"
3. Press Enter
```

#### **Action 6: Show Multiple Log Patterns**
**Point to these logging statements:**

```javascript
// Line 15
logger.info('Fetching all users', {
  operation: 'get_users',
  user_count: users.length,
  request_source: req.ip
});

// Line 55
logger.info('Fetching user by ID', {
  operation: 'get_user_by_id',
  user_id: userId,
  request_source: req.ip
});

// Line 95
logger.info('User found successfully', {
  operation: 'get_user_by_id',
  user_id: userId,
  user_name: user.name
});
```

### **Part C: Generate Log Volume (30 seconds)**

#### **Action 7: Generate Traffic**
**In terminal, run these commands:**
```bash
# Generate multiple requests to create log volume
for i in {1..10}; do curl -s http://localhost:3000/api/users > /dev/null; done
for i in {1..5}; do curl -s http://localhost:3000/ > /dev/null; done
for i in {1..3}; do curl -s http://localhost:3000/api/users/1 > /dev/null; done
```

**Say while running:**
> *"I'm generating traffic to create log volume. The Datadog extension will detect these patterns and show annotations above each logging line."*

### **Part D: Show the Annotations (30 seconds)**

#### **Action 8: Look for Visual Annotations**
**In the code editor, look for:**
- Small gray text above logging lines
- Numbers showing log frequency
- Clickable annotations

**If annotations appear, say:**
> *"See these annotations above our logging code? They show how many times each log line has executed. I can click on any annotation to open the Log Explorer in Datadog and see the actual logs."*

**If annotations don't appear immediately, say:**
> *"The annotations may take a few moments to appear as the extension processes the log data. In a fully configured environment, you'd see real-time metrics above each logging statement."*

---

## 🎯 **What the Annotations Look Like**

### **Expected Visual Annotations:**
```javascript
// 📊 25 logs in last hour ← This appears above the code
logger.info('Homepage accessed', {
  // ... log data
});

// 📊 15 logs in last hour ← This appears above the code  
logger.info('Fetching all users', {
  // ... log data
});
```

### **When You Click an Annotation:**
- Opens Datadog Log Explorer
- Filters to show logs from that specific line
- Shows log volume over time
- Allows deep dive into log details

---

## 🔧 **Troubleshooting During Demo**

### **If Annotations Don't Appear:**

#### **Option 1: Explain the Feature**
> *"In a fully configured production environment, you'd see visual annotations above each logging line showing log volume and frequency. Let me show you what that looks like in the Datadog dashboard instead."*

#### **Option 2: Show Extension Panel**
```
1. Click on Datadog icon in sidebar
2. Show Code Insights panel
3. Point to log-related metrics
```

#### **Option 3: Demonstrate with Log Explorer**
> *"While the annotations are processing, let me show you how this connects to Datadog's Log Explorer where you can see all these logs in real-time."*

---

## 🎬 **Alternative Demo Flow (If Annotations Not Visible)**

### **Focus on the Integration Concept:**

#### **Step 1: Show the Code**
> *"Here's our logging code. The Datadog extension automatically detects these patterns."*

#### **Step 2: Show the Logs**
```
1. Open logs/combined.log
2. Show the structured logs being generated
3. Point out the correlation with the code
```

#### **Step 3: Explain the Value**
> *"In production, these annotations would show above each line, telling you exactly how often each log statement executes. You can click any annotation to jump directly to those logs in Datadog."*

#### **Step 4: Show Log Volume**
```bash
# Show log count
wc -l logs/combined.log
```
> *"We've generated X log entries. The extension would show this volume directly in the IDE."*

---

## 🎯 **Key Messages to Deliver**

### **1. Automatic Detection**
> *"The Datadog extension automatically finds logging patterns in your code - no configuration needed."*

### **2. Real-Time Metrics**
> *"Annotations show live metrics about log frequency and volume."*

### **3. Direct Navigation**
> *"Click any annotation to jump directly to those logs in Datadog Log Explorer."*

### **4. Development Efficiency**
> *"See which parts of your code are generating the most logs without leaving your IDE."*

### **5. Production Insights**
> *"Understand your application's logging patterns during development."*

---

## 📋 **Demo Checklist**

- [ ] Datadog extension visible in sidebar
- [ ] Multiple files with logging code open
- [ ] Terminal ready for generating traffic
- [ ] Log file available as backup
- [ ] Explanation ready if annotations don't appear

---

## ⏱️ **3-Minute Timing**

- **0:00-1:00** - Show logging code in multiple files
- **1:00-1:30** - Generate traffic to create log volume
- **1:30-2:30** - Look for and explain annotations
- **2:30-3:00** - Demonstrate clicking annotations or show alternative

**🎯 Your Datadog Log Annotations demo is ready! 🚀**
