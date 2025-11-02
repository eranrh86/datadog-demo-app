# 🎯 Log Annotations Visual Demo Guide

## 📊 **EXACTLY What to Point Out in the Logs**

### **Sample Log Entry (What You'll See):**
```json
{
  "timestamp": "2025-11-02T07:07:10.606Z",
  "level": "info",
  "message": "Metric gauge",
  "service": "datadog-demo-app",
  "dd": {
    "trace_id": "4889283816924674605",    ← 👆 POINT #1: "Trace Correlation"
    "span_id": "3712526138535361048",     ← 👆 POINT #2: "Span Correlation" 
    "service": "datadog-demo-app",
    "version": "1.0.0",
    "env": "demo"
  },
  "environment": "development",
  "metric_type": "gauge",                 ← 👆 POINT #3: "Custom Metric Type"
  "metric_name": "http.request.duration", ← 👆 POINT #4: "Business Metric Name"
  "metric_value": 69,                     ← 👆 POINT #5: "Actual Value"
  "tags": {                               ← 👆 POINT #6: "Filterable Tags"
    "method": "GET",
    "status_code": "200", 
    "endpoint": "/"
  },
  "dd_custom_metric": true,               ← 👆 POINT #7: "Datadog Flag" ⭐ KEY!
  "log_sequence": 76                      ← 👆 POINT #8: "Volume Tracking"
}
```

---

## 🎬 **Exact Pointing Script**

### **When showing the log entry, say:**

> **"Let me highlight the key Datadog features in this log entry:"**

**👆 Point to each element:**

1. **`"trace_id": "4889283816924674605"`**
   > *"This trace ID correlates this log with APM traces"*

2. **`"span_id": "3712526138535361048"`**  
   > *"The span ID shows exactly which part of the request this log belongs to"*

3. **`"metric_type": "gauge"`**
   > *"This tells Datadog what kind of metric this is - gauge, increment, or histogram"*

4. **`"metric_name": "http.request.duration"`**
   > *"This becomes a queryable metric in Datadog dashboards"*

5. **`"metric_value": 69`**
   > *"The actual measurement - 69 milliseconds response time"*

6. **`"tags": {"method": "GET", "status_code": "200"}`**
   > *"These tags let you filter and group metrics in Datadog"*

7. **`"dd_custom_metric": true`** ⭐ **MOST IMPORTANT**
   > *"This flag tells Datadog to create a metric, not just store a log"*

8. **`"log_sequence": 76`**
   > *"This tracks log volume automatically"*

---

## 🔍 **What to Look For in Different Log Types**

### **1. Gauge Metrics (Current Values):**
```json
{
  "message": "Metric gauge",
  "metric_type": "gauge",
  "metric_name": "users.total_count",
  "metric_value": 3,
  "dd_custom_metric": true
}
```
**Say:** *"Gauges show current state - like how many users we have right now"*

### **2. Increment Metrics (Counters):**
```json
{
  "message": "Metric increment", 
  "metric_type": "increment",
  "metric_name": "http.request.count",
  "metric_value": 1,
  "dd_custom_metric": true
}
```
**Say:** *"Increments count events - like how many requests we've processed"*

### **3. Business Logic Logs:**
```json
{
  "message": "Fetching all users",
  "operation": "get_users",
  "user_count": 3,
  "request_source": "::1"
}
```
**Say:** *"These logs provide business context about what the application is doing"*

---

## 🎯 **Demo Commands & Expected Results**

### **Command 1:**
```bash
curl http://localhost:3000/api/users
```

**What to point out in logs:**
- User count gauge: `"metric_name": "users.total_count"`
- Request duration: `"metric_name": "http.request.duration"`
- Request count: `"metric_name": "http.request.count"`

### **Command 2:**
```bash
curl http://localhost:3000/api/orders
```

**What to point out in logs:**
- Order count gauge: `"metric_name": "orders.total_count"`
- Performance warning if slow: `"performance_issue": true`
- Histogram metric: `"metric_type": "histogram"`

### **Command 3:**
```bash
curl http://localhost:3000/api/health
```

**What to point out in logs:**
- System metrics: `"metric_name": "app.uptime"`
- Memory usage: `"metric_name": "app.memory.used"`
- Health check operation: `"operation": "health_check"`

---

## 🎪 **Trace Correlation Demo**

### **Show Multiple Logs with Same Trace ID:**

**Point out how these logs share the same trace_id:**

```json
// Log Entry 1
{
  "message": "Request started",
  "dd": {"trace_id": "4889283816924674605", "span_id": "1111111111111111111"}
}

// Log Entry 2  
{
  "message": "Fetching all users",
  "dd": {"trace_id": "4889283816924674605", "span_id": "2222222222222222222"}
}

// Log Entry 3
{
  "message": "Request completed", 
  "dd": {"trace_id": "4889283816924674605", "span_id": "3333333333333333333"}
}
```

**Say:** *"Notice all these logs have the same trace_id but different span_ids - this is one request flowing through multiple parts of our application. In Datadog, you can click on any APM trace and see all these related logs."*

---

## 🎯 **Key Messages to Deliver**

### **1. Custom Metrics Creation:**
> *"With just one line of code, we're creating queryable metrics in Datadog that can be used in dashboards, alerts, and analytics."*

### **2. Trace Correlation:**
> *"Every log is automatically correlated with APM traces, giving you complete observability from a single request."*

### **3. Business Context:**
> *"We're not just logging technical data - we're capturing business metrics like user counts, order values, and performance indicators."*

### **4. Structured Data:**
> *"Everything is structured JSON, making it searchable, filterable, and analyzable in Datadog."*

### **5. Automatic Volume Tracking:**
> *"The log_sequence field automatically tracks log volume, helping you understand application activity patterns."*

---

## 🔧 **Troubleshooting During Demo**

### **If logs look different:**
- Look for the key fields: `dd_custom_metric`, `trace_id`, `metric_type`
- The exact values will change, but the structure stays the same

### **If you can't find recent logs:**
```bash
# Get the latest entries
tail -10 logs/combined.log
```

### **If you want prettier formatting:**
```bash
# Pretty print the latest log
tail -1 logs/combined.log | jq .
```

---

## ⏱️ **3-Minute Timing**

- **0:00-0:45** - Show code, explain `dd_custom_metric: true`
- **0:45-1:30** - Run curl commands, generate data
- **1:30-3:00** - Analyze logs, point out 8 key elements

**🎯 You're ready to deliver a perfect log annotations demo! 🚀**
