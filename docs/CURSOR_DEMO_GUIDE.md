# 🎯 Datadog Demo Guide - Cursor IDE Integration

## Pre-Demo Setup (5 minutes before presentation)

### 1. **Start Your Demo Environment**
```bash
cd /path/to/datadog-demo-app
./start-demo.sh
```

### 2. **Open Cursor IDE**
- Open the project: `File` → `Open Folder` → `/path/to/datadog-demo-app`
- Ensure Datadog extension is visible in sidebar

---

## 🎬 **Demo Script - Cursor IDE Integration**

### **PART 1: Log Annotations & Volume Gauging** (3 minutes)

#### **Step 1: Show the Code**
1. **Open** `src/utils/logger.js`
2. **Highlight lines 64-72** (Custom metrics methods):
```javascript
logger.gauge = (metric, value, tags = {}) => {
  logger.info('Metric gauge', {
    metric_type: 'gauge',
    metric_name: metric,
    metric_value: value,
    tags: tags,
    dd_custom_metric: true
  });
};
```

#### **Step 2: Show Usage in Action**
1. **Open** `src/middleware/requestLogger.js`
2. **Highlight lines 32-42** (Log annotations in use):
```javascript
logger.gauge('http.request.duration', duration, {
  method: req.method,
  status_code: res.statusCode.toString(),
  endpoint: req.route?.path || req.url
});
```

#### **Step 3: Generate Live Data**
1. **Open Terminal in Cursor**: `View` → `Terminal`
2. **Run commands**:
```bash
curl http://localhost:3000/api/users
curl http://localhost:3000/api/orders
```

#### **Step 4: Show the Logs**
1. **Open** `logs/combined.log` in Cursor
2. **Point out the annotations**:
   - `dd_custom_metric: true`
   - `metric_type: "gauge"`
   - `trace_id` and `span_id` correlation

---

### **PART 2: Code Insights - Runtime Errors** (4 minutes)

#### **Step 1: Show Intentional Vulnerabilities**
1. **Open** `src/app.js`
2. **Navigate to line 73** (Vulnerable endpoint):
```javascript
// VULNERABILITY: SQL Injection potential
const query = `SELECT * FROM users WHERE id = ${id}`;

// VULNERABILITY: Eval usage  
const result = eval(`"User ID: ${id}"`);
```

#### **Step 2: Show Runtime Error Code**
1. **Navigate to line 95** (Runtime error endpoint):
```javascript
// This will cause a runtime error
const undefinedObject = null;
const result = undefinedObject.someProperty.anotherProperty;
```

#### **Step 3: Trigger Errors from Cursor**
1. **In Terminal**:
```bash
curl http://localhost:3000/vulnerable/123
curl http://localhost:3000/api/users/999
curl http://localhost:3000/error/runtime
```

#### **Step 4: Show Datadog Extension**
1. **Click Datadog icon** in sidebar
2. **Show Code Insights panel**
3. **Point out error detection** (if configured)

---

### **PART 3: View in IDE Integration** (2 minutes)

#### **Step 1: Show Error Stack Traces**
1. **Open** `logs/combined.log`
2. **Find an error entry** and highlight:
```json
{
  "error_stack": "TypeError: Cannot read properties of null...\n    at /path/to/datadog-demo-app/src/routes/users.js:48:43",
  "error_type": "unhandled_exception"
}
```

#### **Step 2: Navigate to Error Location**
1. **Use Cursor's Go to Line**: `Cmd+G`
2. **Type**: `src/routes/users.js:48`
3. **Show the exact error location**

#### **Step 3: Demonstrate IDE Integration**
1. **In Datadog dashboard** (if available):
   - Click "View in IDE" from error trace
   - Show how it opens the exact file/line in Cursor

---

### **PART 4: Static Code Analysis** (2 minutes)

#### **Step 1: Run ESLint from Cursor**
1. **Open Command Palette**: `Cmd+Shift+P`
2. **Type**: `ESLint: Show Output`
3. **Or run in terminal**:
```bash
npm run lint
```

#### **Step 2: Show Security Issues**
1. **Point out the errors**:
   - `eval can be harmful`
   - `Generic Object Injection Sink`
   - `security/detect-eval-with-expression`

#### **Step 3: Show in Problems Panel**
1. **Open Problems panel**: `View` → `Problems`
2. **Show linting errors with file locations**
3. **Click on errors to navigate to code**

---

### **PART 5: Exception Replay** (3 minutes)

#### **Step 1: Show Error Handling Code**
1. **Open** `src/middleware/errorHandler.js`
2. **Highlight lines 5-20** (Comprehensive error logging):
```javascript
logger.error('Unhandled error occurred', {
  error_message: err.message,
  error_stack: err.stack,
  request_method: req.method,
  request_url: req.url,
  request_headers: req.headers,
  request_body: req.body,
  // ... full context
});
```

#### **Step 2: Generate Rich Error Context**
1. **In Terminal**:
```bash
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"userId":"invalid","product":"Test"}'
```

#### **Step 3: Show the Rich Context**
1. **Open** `logs/combined.log`
2. **Find the error entry**
3. **Highlight the rich context**:
   - Full request details
   - Headers and body
   - Stack trace
   - Environment info

---

### **PART 6: Flaky Test Detection** (2 minutes)

#### **Step 1: Show Flaky Test Code**
1. **Open** `tests/users.test.js`
2. **Navigate to line 50** (Flaky test):
```javascript
test('flaky test - sometimes fails randomly', async () => {
  const shouldFail = Math.random() < 0.3;
  
  if (shouldFail) {
    throw new Error('Flaky test failure - network timeout simulation');
  }
  // ...
});
```

#### **Step 2: Run Tests from Cursor**
1. **Open Command Palette**: `Cmd+Shift+P`
2. **Type**: `Tasks: Run Task`
3. **Select**: `npm: test`
4. **Or in terminal**:
```bash
npm test
```

#### **Step 3: Show Flaky Results**
1. **Run tests multiple times**:
```bash
npm test
npm test  
npm test
```
2. **Show different results each time**
3. **Point out the random failures**

---

## 🎯 **Cursor-Specific Demo Features**

### **1. Datadog Extension Panel**
- **Location**: Sidebar (Datadog icon)
- **Features to show**:
  - Code Insights view
  - Service overview
  - Error tracking
  - Performance metrics

### **2. Integrated Terminal**
- **Show live log streaming**:
```bash
tail -f logs/combined.log | jq .
```

### **3. Problems Panel Integration**
- **View** → **Problems**
- **Show security vulnerabilities**
- **Click to navigate to issues**

### **4. Command Palette Integration**
- **Cmd+Shift+P** → **Datadog**
- **Show available Datadog commands**

### **5. File Navigation**
- **Cmd+P** → **Quick file search**
- **Cmd+G** → **Go to line** (for error locations)

---

## 🎬 **Demo Flow Summary**

1. **Start** → Show code structure in Cursor
2. **Log Annotations** → Live code + terminal output
3. **Code Insights** → Static analysis in Problems panel
4. **View in IDE** → Navigate from logs to code
5. **Exception Replay** → Rich error context
6. **Flaky Tests** → Run tests in integrated terminal
7. **Finish** → Show Datadog extension panel

---

## 🔧 **Cursor Shortcuts for Demo**

| Action | Shortcut | Purpose |
|--------|----------|---------|
| Command Palette | `Cmd+Shift+P` | Access Datadog commands |
| Quick Open | `Cmd+P` | Navigate to files quickly |
| Go to Line | `Cmd+G` | Jump to error locations |
| Toggle Terminal | `Cmd+J` | Show/hide terminal |
| Problems Panel | `Cmd+Shift+M` | Show linting errors |
| Search | `Cmd+Shift+F` | Find code patterns |

---

## 📋 **Pre-Demo Checklist**

- [ ] Demo app running (`./start-demo.sh`)
- [ ] Cursor open with project loaded
- [ ] Datadog extension visible and configured
- [ ] Terminal panel open
- [ ] `logs/combined.log` ready to view
- [ ] Test files open in tabs
- [ ] Problems panel accessible

**Your Cursor IDE demo is ready! 🚀**
