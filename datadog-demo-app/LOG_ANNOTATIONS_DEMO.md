# 🎯 Log Annotations Demo - Step-by-Step Script (3 minutes)

## 📋 **Pre-Demo Setup**
- ✅ Demo app running: `./start-demo.sh`
- ✅ Cursor open with project loaded
- ✅ Terminal panel visible (`Cmd+J`)

---

## 🎬 **STEP-BY-STEP DEMO SCRIPT**

### **STEP 1: Show the Custom Metrics Code (45 seconds)**

#### **Action 1.1: Open the Logger File**
```
1. Press Cmd+P (Quick Open)
2. Type: "logger.js"
3. Press Enter to open src/utils/logger.js
```

#### **Action 1.2: Navigate to Custom Methods**
```
1. Press Cmd+G (Go to Line)
2. Type: "64"
3. Press Enter
```

#### **Action 1.3: Highlight the Code (SAY THIS):**
> **"Here's where we create custom log annotations for Datadog. Let me show you the three key methods we've built:"**

**Point to lines 64-72:**
```javascript
logger.gauge = (metric, value, tags = {}) => {
  logger.info('Metric gauge', {
    metric_type: 'gauge',
    metric_name: metric,
    metric_value: value,
    tags: tags,
    dd_custom_metric: true  // ← POINT THIS OUT!
  });
};
```

#### **Action 1.4: Explain Key Features (SAY THIS):**
> **"Notice the `dd_custom_metric: true` flag - this tells Datadog this is a custom business metric, not just a regular log entry. We also have increment and histogram methods."**

---

### **STEP 2: Show Usage in Application Code (30 seconds)**

#### **Action 2.1: Open Request Logger**
```
1. Press Cmd+P
2. Type: "requestLogger.js"
3. Press Enter
```

#### **Action 2.2: Navigate to Usage**
```
1. Press Cmd+G
2. Type: "32"
3. Press Enter
```

#### **Action 2.3: Highlight Usage (SAY THIS):**
> **"Here's how we use these annotations in our middleware to track every HTTP request:"**

**Point to lines 32-42:**
```javascript
// Log volume and performance metrics
logger.gauge('http.request.duration', duration, {
  method: req.method,
  status_code: res.statusCode.toString(),
  endpoint: req.route?.path || req.url
});

logger.increment('http.request.count', 1, {
  method: req.method,
  status_code: res.statusCode.toString(),
  endpoint: req.route?.path || req.url
});
```

---

### **STEP 3: Generate Live Data (45 seconds)**

#### **Action 3.1: Open Terminal**
```
1. Click on Terminal panel (or press Cmd+J if not visible)
2. Make sure you're in the project directory
```

#### **Action 3.2: Run Commands (SAY THIS):**
> **"Now let's generate some live data and watch the log annotations in action:"**

**Type and execute these commands one by one:**
```bash
curl http://localhost:3000/api/users
```

**Wait 2 seconds, then:**
```bash
curl http://localhost:3000/api/orders
```

**Wait 2 seconds, then:**
```bash
curl http://localhost:3000/api/health
```

#### **Action 3.3: Explain What's Happening (SAY THIS):**
> **"Each request is now generating structured logs with custom metrics, trace correlation, and business context. Let's see the actual log entries."**

---

### **STEP 4: View Live Logs (60 seconds)**

#### **Action 4.1: Open Log File**
```
1. Press Cmd+P
2. Type: "combined.log"
3. Press Enter to open logs/combined.log
```

#### **Action 4.2: Go to Bottom of File**
```
1. Press Cmd+End (or Cmd+Down Arrow)
2. Scroll to see the latest entries
```

#### **Action 4.3: Highlight Key Elements (SAY THIS):**
> **"Look at these beautiful structured log entries. Let me highlight the key Datadog features:"**

**Point to a log entry like this:**
```json
{
  "timestamp": "2025-11-02T06:58:42.350Z",
  "level": "info",
  "message": "Metric gauge",
  "service": "datadog-demo-app",
  "dd": {
    "trace_id": "525320546303301229",     ← POINT: "Trace correlation"
    "span_id": "881555568409080332",      ← POINT: "Span correlation"
    "service": "datadog-demo-app",
    "version": "1.0.0",
    "env": "demo"
  },
  "environment": "development",
  "metric_type": "gauge",                 ← POINT: "Custom metric type"
  "metric_name": "users.total_count",     ← POINT: "Business metric"
  "metric_value": 3,                      ← POINT: "Actual value"
  "tags": {},                             ← POINT: "Filterable tags"
  "dd_custom_metric": true,               ← POINT: "Datadog flag"
  "log_sequence": 59                      ← POINT: "Volume tracking"
}
```

#### **Action 4.4: Show Different Metric Types (SAY THIS):**
> **"Notice we have different types of annotations - gauges for current values, increments for counters, and histograms for distributions."**

**Scroll to find examples of:**
- `"metric_type": "gauge"` - Current values
- `"metric_type": "increment"` - Counters  
- `"metric_type": "histogram"` - Distributions

---

### **STEP 5: Demonstrate Trace Correlation (30 seconds)**

#### **Action 5.1: Generate New Request**
**In terminal, run:**
```bash
curl http://localhost:3000/
```

#### **Action 5.2: Find Correlated Logs (SAY THIS):**
> **"Watch how all logs from the same request share the same trace_id - this is how Datadog correlates logs with APM traces:"**

**In the log file, point to multiple entries with the same trace_id:**
```json
// Entry 1
"dd": {
  "trace_id": "6286597098538647130",  ← SAME TRACE ID
  "span_id": "4795722115088530944"
}

// Entry 2  
"dd": {
  "trace_id": "6286597098538647130",  ← SAME TRACE ID
  "span_id": "3166024478966362874"    ← DIFFERENT SPAN
}
```

#### **Action 5.3: Explain the Power (SAY THIS):**
> **"This trace correlation means in Datadog, you can click on any APM trace and see all the related logs, or click on a log and see the full distributed trace. It's complete observability."**

---

## 🎯 **Key Points to Emphasize**

### **1. Custom Metrics Flag**
- Point out `dd_custom_metric: true`
- Explain it creates Datadog metrics, not just logs

### **2. Trace Correlation**  
- Show `trace_id` and `span_id` in logs
- Explain how it links logs to APM traces

### **3. Business Context**
- Highlight `metric_name` like "users.total_count"
- Show `tags` for filtering and grouping

### **4. Structured Data**
- Point out JSON format
- Show consistent schema across all logs

### **5. Volume Tracking**
- Highlight `log_sequence` incrementing
- Explain automatic volume gauging

---

## 🎬 **Exact Words to Say**

### **Opening (15 seconds):**
> *"Let me show you how we implement log annotations to gauge log volumes and create custom metrics directly from our application code."*

### **Code Explanation (30 seconds):**
> *"Here in our logger utility, we've created custom methods that automatically add Datadog-specific metadata. The key is this `dd_custom_metric: true` flag that tells Datadog to treat these as business metrics, not just log entries."*

### **Live Demo (45 seconds):**
> *"Now watch what happens when I make some API calls. Each request generates structured logs with trace correlation, custom metrics, and business context."*

### **Log Analysis (60 seconds):**
> *"Look at these beautiful structured logs. Every entry has a trace_id that correlates with APM traces, custom metric data that becomes queryable in Datadog, and business context like user counts and response times. This is how you get complete observability."*

### **Closing (30 seconds):**
> *"This trace correlation is the magic - click on any trace in Datadog APM and you'll see all related logs. Click on any log and you'll see the full distributed trace. It's seamless integration between logs, metrics, and traces."*

---

## 🔧 **Backup Commands (If Needed)**

### **If logs aren't updating:**
```bash
# Refresh the log file
tail -5 logs/combined.log
```

### **If you need more data:**
```bash
# Generate multiple requests
for i in {1..3}; do curl http://localhost:3000/api/users; sleep 1; done
```

### **If you want pretty JSON:**
```bash
# Stream logs with pretty formatting
tail -f logs/combined.log | jq .
```

---

## ⏱️ **Timing Breakdown**

- **0:00-0:45** - Show custom metrics code
- **0:45-1:15** - Show usage in application  
- **1:15-2:00** - Generate live data with curl
- **2:00-3:00** - Analyze logs and trace correlation

**Total: 3 minutes**

---

## 🎯 **Success Criteria**

By the end of this demo, your audience should understand:
- ✅ How to create custom log annotations
- ✅ What `dd_custom_metric: true` does
- ✅ How trace correlation works
- ✅ The value of structured logging
- ✅ How logs become queryable metrics in Datadog

**You're ready to nail this demo! 🚀**
