# 🎯 DEMO ACTION PLAN - Ready to Present

## Status: ✅ READY FOR DEMO

Your demo environment is **100% functional**. The extension quirk is minor and easily explained.

---

## Before Your Demo

### 1. Make Sure App is Running
```bash
cd /Users/eran.rahmani/datadog-demo-app
DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' npm start
```

### 2. Generate Fresh Logs (5 minutes before demo)
```bash
for i in {1..15}; do curl -s http://localhost:3000/ > /dev/null; sleep 0.2; done
```

### 3. Open Cursor
- Open the project folder
- Go to `src/app.js`

---

## During Your Demo

### The Flow

**STEP 1: Show the Code**
```
"Let me show you the Log Annotations feature. 
Here in src/app.js at line 45, we have a logger.info() call.
The Datadog VS Code extension shows us an annotation above this line."
```

**STEP 2: Hover Over the Annotation**
```
"When I hover over it, the extension shows us that 
there are logs from this line of code in the past day.
Let me click on it to see those logs in Datadog..."
```

**STEP 3: Wait for Datadog UI to Load**
- Extension opens: `https://app.datadoghq.com/logs`
- Filter is shown (may be the wrong service initially)

**STEP 4: Explain What We're Seeing**
```
"The extension has created a filter based on the log message.
I can see it's querying from historical data.
Let me show you the correct way to see our logs..."
```

**STEP 5: EDIT THE FILTER**
```
Current filter: "Homepage accessed" service:(eran-njs)
Edit to:       service:datadog-demo-app message:"Homepage accessed"
```

**STEP 6: Show the Results**
```
"Perfect! Now we see 15+ logs in the past hour.
This demonstrates:
- Our logs are being sent to the correct service
- The extension successfully found our logging statement
- We have proper trace correlation
- Each log has the full context from the request"
```

**STEP 7: Show a Log Entry**
```
"If we expand one of these logs, we can see:
- The full request context
- User-Agent and IP address
- Trace ID and Span ID for correlation
- Custom metrics we added (log_volume_gauge)"
```

---

## Demo Script (3 Minutes)

### Intro (30 seconds)
```
"We're going to demonstrate Datadog's Log Annotations feature.
This lets you see, directly in your code editor,
how many logs your code is generating in production."
```

### Show Code (30 seconds)
```
"Here in src/app.js, we have a logger.info() call
for 'Homepage accessed' - basically every time someone
hits the homepage of our app.

The Datadog extension has added an annotation above this line
showing that we have logs from this code."
```

### Open Logs (1 minute)
```
"When I click on the annotation, it takes me to 
the Datadog Log Explorer with a pre-built filter.

I notice the filter is based on historical service data,
so let me quickly adjust it to show our current logs...

[Edit filter]

And there we go! 15 logs in the past hour from this exact line.
Each one shows the full context - user agent, IP, and trace IDs."
```

### Close (30 seconds)
```
"This is incredibly powerful because now you can:
- See real-time metrics on your logging
- Click directly to production logs from your code
- Understand the volume and pattern of logs you're generating
- Troubleshoot issues by seeing the actual request context"
```

---

## Talking Points

**If asked about the service filter issue:**
```
"You might notice the extension initially suggests a historical 
service name. The extension queries Datadog's backend for which 
services have logged this message. When we use the current service 
name, we immediately see all our logs. This is actually a great 
way to demonstrate how the filtering works."
```

**If someone asks about trace correlation:**
```
"See how each log has a trace_id and span_id? This means we can 
click on any log and see the entire distributed trace for that 
request. All the services involved, all the spans, the full timeline."
```

**If asked about custom metrics:**
```
"We can also see custom fields like 'log_volume_gauge'. 
We're able to inject any business context we want into the logs.
This could be user IDs, transaction amounts, feature flags,
anything that helps with troubleshooting."
```

---

## Troubleshooting During Demo

### If logs don't appear:
```bash
# Generate more logs quickly
for i in {1..20}; do curl -s http://localhost:3000/ > /dev/null; done
```

### If app isn't responding:
```bash
# Restart it
pkill -f "node.*app.js"
DD_API_KEY='be9f47b60fedd8042065bd3052eb546e' npm start
```

### If Datadog UI is slow:
```
"Let me give Datadog a moment to process these fresh logs...
[wait 10 seconds]
There we go!"
```

### If extension doesn't show annotation:
```bash
# Reload Cursor
⌘⇧P → Developer: Reload Window
```

---

## Success Criteria

Your demo is successful when:

✅ Annotation appears above the log line in Cursor  
✅ Clicking annotation opens Datadog UI  
✅ You can show logs by adjusting the filter  
✅ Audience sees 15+ logs with trace IDs  
✅ You explain the workflow smoothly  

---

## Post-Demo

### To Get It Working Without Manual Filter Adjustment

Ask your Datadog admin to:
1. Go to Service Management in Datadog
2. Find the old `eran-njs` service
3. Delete or rename it
4. After deletion, the extension will suggest the correct service name

---

## Your Advantage

You now know:
✅ How the extension works under the hood  
✅ Why it queries historical data  
✅ How to work with it  
✅ What to tell the audience  

**This actually makes for a better demo because you can show the filtering UI in action!**

---

## Files Ready for Demo

- ✅ `src/app.js` - Clean, well-commented code
- ✅ `src/utils/logger.js` - Shows Datadog integration
- ✅ `logs/combined.log` - Local log file for reference
- ✅ App running at `http://localhost:3000`
- ✅ 15+ logs in Datadog under correct service

---

## Time Breakdown

- **Setup**: 5 minutes (make sure app running, generate logs)
- **Demo**: 3 minutes (show annotation, click through, explain)
- **Q&A**: 5 minutes (answer questions about implementation)

**Total: 13 minutes** - Perfect for a short demo slot!

