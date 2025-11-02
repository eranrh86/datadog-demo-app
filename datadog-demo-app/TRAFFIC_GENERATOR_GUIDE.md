# 🚀 Continuous Traffic Generator - User Guide

## ✅ Background Log & Trace Generator Running!

Your traffic generator is now running in the background, generating logs and traces every minute.

---

## 🎯 Quick Commands

### **Check Status**
```bash
./traffic-generator.sh status
```
Shows if running, PID, runtime, and recent activity

### **View Live Logs**
```bash
./traffic-generator.sh logs
```
Tail the traffic generator logs (Ctrl+C to stop viewing)

### **Stop Generator**
```bash
./traffic-generator.sh stop
```
Stops the background traffic generator

### **Restart Generator**
```bash
./traffic-generator.sh restart
```
Stops and starts the generator

---

## 📊 What It Generates

**Every 60 seconds (1 minute):**

1. **Homepage** - 3 requests
   - Generates: "Homepage accessed" logs
   - Creates: Trace spans with correlation

2. **Health Check** - 1 request
   - Generates: "Health check performed" logs
   - Reports: App uptime and memory metrics

3. **Users API** - 2 requests
   - `/api/users` - List all users
   - `/api/users/1` - Get specific user
   - Generates: "Fetching all users" logs

4. **Orders API** - 1 request
   - `/api/orders` - List all orders
   - Generates: "Fetching all orders" logs
   - May trigger: Slow query warning (performance monitoring)

5. **Error Trace** - Every 5 minutes
   - `/api/users/999` - Non-existent user
   - Generates: Error logs with stack traces
   - Creates: Error spans for error tracking

**Total:** 8+ logs & traces per cycle

---

## 📈 Expected Volume

| Timeframe | Logs Generated | Traces Generated |
|-----------|----------------|------------------|
| 1 minute  | 8+             | 8+               |
| 1 hour    | 480+           | 480+             |
| 24 hours  | 11,520+        | 11,520+          |

---

## 🔍 View Your Logs in Datadog

### **All Logs**
```
https://app.datadoghq.com/logs?query=service:datadog-demo-app
```

### **Recent Logs (Last 15 minutes)**
```
https://app.datadoghq.com/logs?query=service:datadog-demo-app&from_ts=now-15m
```

### **Homepage Logs**
```
https://app.datadoghq.com/logs?query=service:datadog-demo-app%20message:%22Homepage%20accessed%22
```

### **Error Logs**
```
https://app.datadoghq.com/logs?query=service:datadog-demo-app%20status:error
```

---

## 🔗 View Traces in Datadog

### **All Traces**
```
https://app.datadoghq.com/apm/traces?query=service:datadog-demo-app
```

### **Service Map**
```
https://app.datadoghq.com/apm/service/datadog-demo-app
```

### **Performance Dashboard**
```
https://app.datadoghq.com/apm/service/datadog-demo-app/operations
```

---

## 📁 Log Files

**Traffic Generator Logs:**
```bash
tail -f logs/traffic-generator.log
```

**Application Logs:**
```bash
tail -f logs/combined.log
```

**Application Runtime:**
```bash
tail -f logs/app-runtime.log
```

---

## ⚙️ Configuration

**File:** `generate-logs-continuously.sh`

**Change interval:**
```bash
INTERVAL=60  # Change to desired seconds
```

**Endpoints hit:**
- `/` - Homepage
- `/api/health` - Health check
- `/api/users` - Users list
- `/api/users/1` - Specific user
- `/api/orders` - Orders list
- `/api/users/999` - Error generator (every 5 cycles)

---

## 🛑 Stopping the Generator

### **Method 1: Using Manager Script**
```bash
./traffic-generator.sh stop
```

### **Method 2: Manual Kill**
```bash
cat .traffic-generator.pid
kill <PID>
```

### **Method 3: Kill All**
```bash
pkill -f generate-logs-continuously
```

---

## ✅ Verification

### **Check if Running**
```bash
./traffic-generator.sh status
```

### **Check Recent Activity**
```bash
tail -20 logs/traffic-generator.log
```

### **Count Logs Generated**
```bash
wc -l logs/combined.log
```

### **Check in Datadog** (after 2-3 minutes)
1. Go to: https://app.datadoghq.com/logs
2. Filter: `service:datadog-demo-app`
3. Time range: Last 15 minutes
4. Should see logs increasing every minute

---

## 🎯 Use Cases

### **Demo/Presentation**
- Generates realistic traffic patterns
- Creates diverse log types
- Shows error handling
- Demonstrates trace correlation

### **Testing**
- Volume testing (11k+ logs per day)
- Error tracking validation
- Performance monitoring
- Log aggregation testing

### **Development**
- Continuous data for debugging
- Real-time log stream
- Trace correlation testing
- Metric generation

---

## 🔧 Troubleshooting

### **Generator Not Starting**

**Check if port 3000 is available:**
```bash
lsof -ti:3000
```

**Check logs:**
```bash
cat logs/traffic-generator.log
```

**Manually start app:**
```bash
DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' \
DD_SERVICE='datadog-demo-app' \
npm start
```

### **No Logs Appearing in Datadog**

**Check app is running:**
```bash
curl http://localhost:3000/api/health
```

**Check logs locally:**
```bash
tail -20 logs/combined.log
```

**Verify Datadog HTTP transport:**
```bash
grep "Datadog HTTP transport" logs/app-runtime.log
```

### **Generator Stopped Unexpectedly**

**Check for errors:**
```bash
tail -50 logs/traffic-generator.log
```

**Restart:**
```bash
./traffic-generator.sh restart
```

---

## 📊 Monitoring the Generator

### **Real-time Monitoring**

**Terminal 1: Watch Generator**
```bash
watch -n 5 './traffic-generator.sh status'
```

**Terminal 2: Tail Logs**
```bash
tail -f logs/combined.log | grep "Homepage accessed"
```

**Terminal 3: Datadog**
Open: https://app.datadoghq.com/logs?query=service:datadog-demo-app

---

## 🎉 Summary

**Status:** ✅ Running in background

**What's Happening:**
- Every 60 seconds, generates 8+ logs & traces
- All logs sent to Datadog with service: `datadog-demo-app`
- Includes: Info logs, error logs, trace spans, custom metrics
- Runs continuously until stopped

**Commands:**
```bash
./traffic-generator.sh status   # Check status
./traffic-generator.sh logs     # View logs
./traffic-generator.sh stop     # Stop generator
```

**View in Datadog:**
https://app.datadoghq.com/logs?query=service:datadog-demo-app

---

**Your logs and traces are now being generated continuously!** 🎯

**Last Updated:** November 2, 2025
**Status:** Active and running

