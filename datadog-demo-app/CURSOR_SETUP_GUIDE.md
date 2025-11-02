# 🖥️ Cursor IDE Setup for Datadog Demo

## 📋 **Pre-Demo Cursor Setup**

### **1. Open Project in Cursor**
```bash
# From terminal
cursor /Users/eran.rahmani/datadog-demo-app

# Or from Cursor: File → Open Folder → datadog-demo-app
```

### **2. Recommended Tab Layout**
Open these files in tabs (in order):

1. **`CURSOR_DEMO_GUIDE.md`** - Your demo script
2. **`src/utils/logger.js`** - Log annotations code
3. **`src/app.js`** - Main app with vulnerabilities  
4. **`src/middleware/errorHandler.js`** - Exception handling
5. **`tests/users.test.js`** - Flaky tests
6. **`logs/combined.log`** - Live logs (keep refreshing)

### **3. Panel Configuration**

#### **Left Sidebar:**
- ✅ **Explorer** (file tree)
- ✅ **Datadog Extension** (should be visible)
- ✅ **Search**

#### **Bottom Panel:**
- ✅ **Terminal** (`View` → `Terminal`)
- ✅ **Problems** (`View` → `Problems`)
- ✅ **Output** (for ESLint results)

#### **Right Panel:**
- ✅ **Outline** (code structure)

---

## 🎯 **Step-by-Step Demo Walkthrough**

### **DEMO PART 1: Log Annotations (3 minutes)**

#### **What to Show in Cursor:**

1. **File: `src/utils/logger.js`**
   - **Navigate to lines 64-90**
   - **Highlight the custom methods:**
   ```javascript
   logger.gauge = (metric, value, tags = {}) => {
     logger.info('Metric gauge', {
       metric_type: 'gauge',
       metric_name: metric,
       metric_value: value,
       tags: tags,
       dd_custom_metric: true  // ← Point this out!
     });
   };
   ```

2. **File: `src/middleware/requestLogger.js`**
   - **Navigate to lines 32-42**
   - **Show usage in action:**
   ```javascript
   logger.gauge('http.request.duration', duration, {
     method: req.method,
     status_code: res.statusCode.toString(),
     endpoint: req.route?.path || req.url
   });
   ```

3. **Terminal Commands:**
   ```bash
   curl http://localhost:3000/api/users
   curl http://localhost:3000/api/orders
   ```

4. **File: `logs/combined.log`**
   - **Refresh the file** (`Cmd+R`)
   - **Point out the JSON structure:**
   ```json
   {
     "dd_custom_metric": true,
     "metric_type": "gauge",
     "trace_id": "525320546303301229"
   }
   ```

---

### **DEMO PART 2: Code Insights (4 minutes)**

#### **What to Show in Cursor:**

1. **File: `src/app.js`**
   - **Navigate to line 73** (SQL injection):
   ```javascript
   // VULNERABILITY: SQL Injection potential
   const query = `SELECT * FROM users WHERE id = ${id}`;
   ```
   - **Navigate to line 78** (eval vulnerability):
   ```javascript
   // VULNERABILITY: Eval usage
   const result = eval(`"User ID: ${id}"`);
   ```

2. **Problems Panel** (`Cmd+Shift+M`):
   - **Show ESLint errors:**
     - `eval can be harmful`
     - `security/detect-eval-with-expression`
   - **Click on errors to navigate to code**

3. **Terminal Commands:**
   ```bash
   npm run lint
   ```

4. **Show Output Panel:**
   - **View** → **Output**
   - **Select "ESLint" from dropdown**
   - **Show security warnings**

---

### **DEMO PART 3: View in IDE (2 minutes)**

#### **What to Show in Cursor:**

1. **Generate an error:**
   ```bash
   curl http://localhost:3000/api/users/999
   ```

2. **File: `logs/combined.log`**
   - **Find the error entry**
   - **Highlight the stack trace:**
   ```json
   {
     "error_stack": "TypeError: Cannot read properties of null...\n    at /Users/eran.rahmani/datadog-demo-app/src/routes/users.js:48:43"
   }
   ```

3. **Navigate to Error:**
   - **Press `Cmd+G`**
   - **Type:** `src/routes/users.js:48`
   - **Show the exact error line**

4. **Demonstrate IDE Integration:**
   - **Show how Datadog would link back to this exact location**

---

### **DEMO PART 4: Exception Replay (3 minutes)**

#### **What to Show in Cursor:**

1. **File: `src/middleware/errorHandler.js`**
   - **Navigate to lines 5-25**
   - **Highlight comprehensive logging:**
   ```javascript
   logger.error('Unhandled error occurred', {
     error_message: err.message,
     error_stack: err.stack,
     request_method: req.method,
     request_url: req.url,
     request_headers: req.headers,
     request_body: req.body,
     user_agent: req.get('User-Agent'),
     ip_address: req.ip,
     // ... full context
   });
   ```

2. **Generate Rich Error:**
   ```bash
   curl -X POST http://localhost:3000/api/orders \
     -H "Content-Type: application/json" \
     -d '{"userId":"invalid","product":"Test"}'
   ```

3. **File: `logs/combined.log`**
   - **Show the rich error context**
   - **Point out all the captured data**

---

### **DEMO PART 5: Flaky Tests (2 minutes)**

#### **What to Show in Cursor:**

1. **File: `tests/users.test.js`**
   - **Navigate to line 50**
   - **Show flaky test code:**
   ```javascript
   test('flaky test - sometimes fails randomly', async () => {
     const shouldFail = Math.random() < 0.3; // 30% failure rate
     
     if (shouldFail) {
       throw new Error('Flaky test failure - network timeout simulation');
     }
   });
   ```

2. **Run Tests in Terminal:**
   ```bash
   npm test
   npm test  # Run again to show different results
   npm test  # Run third time
   ```

3. **Show Test Results:**
   - **Point out the random failures**
   - **Highlight flaky test detection**

---

## 🎯 **Cursor-Specific Features to Highlight**

### **1. Integrated Terminal**
- **Show live log streaming:**
  ```bash
  tail -f logs/combined.log | jq .
  ```

### **2. Quick Navigation**
- **`Cmd+P`** → Quick file search
- **`Cmd+G`** → Go to line (for error locations)
- **`Cmd+Shift+F`** → Global search

### **3. Problems Panel Integration**
- **Real-time linting errors**
- **Click to navigate to issues**
- **Security vulnerability highlighting**

### **4. Datadog Extension Panel**
- **Show in sidebar**
- **Code Insights view**
- **Service metrics**

---

## 🎬 **Demo Timing**

| Part | Duration | Focus |
|------|----------|-------|
| Setup | 1 min | Show Cursor layout |
| Log Annotations | 3 min | Code + live output |
| Code Insights | 4 min | Static analysis |
| View in IDE | 2 min | Error navigation |
| Exception Replay | 3 min | Rich context |
| Flaky Tests | 2 min | Test reliability |

**Total: 15 minutes**

---

## 🔧 **Troubleshooting During Demo**

### **If file doesn't refresh:**
- **Press `Cmd+R`** to reload file
- **Or close and reopen the file**

### **If terminal is not visible:**
- **Press `Cmd+J`** to toggle terminal

### **If Datadog extension missing:**
- **Check sidebar for Datadog icon**
- **Or `Cmd+Shift+P` → "Extensions: Show Installed Extensions"**

### **If app stops responding:**
```bash
lsof -ti:3000 | xargs kill -9
./start-demo.sh
```

---

## 📋 **Final Checklist**

Before starting your demo:

- [ ] Cursor open with project loaded
- [ ] All demo files open in tabs
- [ ] Terminal panel visible
- [ ] Problems panel accessible
- [ ] Demo app running (`./start-demo.sh`)
- [ ] Datadog extension visible
- [ ] `CURSOR_DEMO_GUIDE.md` open for reference

**🚀 Your Cursor IDE demo is perfectly set up!**
