# 🤖 Fix in Chat - Cursor Integration Guide

**Feature:** AI-powered code fixes directly in your IDE  
**Repository:** https://github.com/eranrh86/datadog-demo-app  
**Service:** `datadog-demo-app`

---

## 🎯 What is Fix in Chat?

**Fix in Chat** is a Cursor-exclusive feature that uses AI to:
- ✅ Fix code errors automatically
- ✅ Resolve security vulnerabilities
- ✅ Fix flaky tests
- ✅ Provide explanations and context
- ✅ Suggest best practices

It integrates Datadog's error tracking with Cursor's AI to provide intelligent, context-aware fixes.

---

## ✅ Configuration

### 1. Cursor Settings

The `.cursor/settings.json` file is configured with:

```json
{
  "datadog.enabled": true,
  "datadog.service": "datadog-demo-app",
  "datadog.env": "demo",
  "datadog.fixInChat.enabled": true,
  "datadog.codeInsights.enabled": true,
  "datadog.errorTracking.enabled": true,
  "datadog.sourceCodeIntegration.enabled": true,
  "datadog.repository": "https://github.com/eranrh86/datadog-demo-app"
}
```

### 2. Datadog Configuration

The `.datadog/config.json` file includes:

```json
{
  "site": "datadoghq.com",
  "apiKey": "your_api_key",
  "service": "datadog-demo-app",
  "env": "demo",
  "version": "1.0.0"
}
```

### 3. Error Context

All errors include rich context for AI analysis:
- Full stack traces
- Error messages
- File locations
- Code context
- Request/response data
- Environment state

---

## 🎬 How to Use Fix in Chat

### Method 1: From Datadog Error Tracking

1. **Go to Datadog:** APM → Error Tracking
2. **Click on an error**
3. **Click "Fix in Chat"** button
4. **Cursor opens** with error context
5. **AI suggests fix** with explanation
6. **Apply or modify** the fix

### Method 2: From Cursor Directly

1. **Open file with error** (e.g., `src/routes/users.js`)
2. **Cursor shows error** inline
3. **Click on error** or use Cmd+K
4. **Ask:** "Fix this error using Datadog context"
5. **AI provides fix** with explanation

### Method 3: From Linter Errors

1. **Run:** `npm run lint`
2. **See errors** in terminal
3. **Open file** in Cursor
4. **Select error line**
5. **Use Cmd+K:** "Fix this security vulnerability"
6. **AI suggests fix**

---

## 🧪 Demo Scenarios

### Scenario 1: Fix Null Pointer Exception

**Error Location:** `src/routes/users.js:48`

**Current Code:**
```javascript
if (userId === 999) {
  // This will cause a runtime error for demo purposes
  const undefinedUser = null;
  return res.json({ user: undefinedUser.profile.details });
}
```

**Steps:**
1. Trigger error: `curl http://localhost:3000/api/users/999`
2. In Datadog: Click error → "Fix in Chat"
3. Cursor opens with context
4. AI suggests fix:

```javascript
if (userId === 999) {
  // Return proper error response instead of causing null pointer
  logger.error('Demo error: User 999 not found', {
    operation: 'get_user_by_id',
    user_id: userId
  });
  return res.status(404).json({ 
    error: 'User not found',
    message: 'User 999 is used for demo purposes',
    user_id: userId
  });
}
```

**AI Explanation:**
> "The error occurs because you're trying to access properties on a null object. Instead of causing a runtime error, return a proper 404 response with error details. This provides better error handling and debugging information."

---

### Scenario 2: Fix SQL Injection Vulnerability

**Error Location:** `src/app.js:84`

**Current Code:**
```javascript
// VULNERABILITY: SQL Injection potential
const query = `SELECT * FROM users WHERE id = ${id}`;
```

**Steps:**
1. Run: `npm run lint`
2. See: "SQL injection vulnerability detected"
3. Open `src/app.js` in Cursor
4. Select line 84
5. Cmd+K: "Fix this SQL injection vulnerability"

**AI Suggests:**
```javascript
// Fixed: Use parameterized query to prevent SQL injection
const query = 'SELECT * FROM users WHERE id = ?';
const params = [id];
// Execute with: db.query(query, params)
```

**AI Explanation:**
> "SQL injection occurs when user input is directly concatenated into SQL queries. Use parameterized queries or prepared statements instead. This ensures user input is properly escaped and prevents malicious SQL code execution."

---

### Scenario 3: Fix Eval Usage

**Error Location:** `src/app.js:87`

**Current Code:**
```javascript
// VULNERABILITY: Eval usage
const result = eval(`"User ID: ${id}"`);
```

**Steps:**
1. ESLint detects: "eval can be harmful"
2. In Cursor: Click error
3. Ask: "Fix this eval vulnerability"

**AI Suggests:**
```javascript
// Fixed: Use template literals instead of eval
const result = `User ID: ${id}`;
```

**AI Explanation:**
> "The eval() function executes arbitrary JavaScript code and is a major security risk. In this case, you're just creating a string, so use template literals instead. This is safer, faster, and achieves the same result."

---

### Scenario 4: Fix Object Injection

**Error Location:** `src/routes/users.js:146`

**Current Code:**
```javascript
// VULNERABILITY: No input sanitization (for Code Insights demo)
Object.assign(users[userIndex], updates);
```

**Steps:**
1. ESLint detects: "Object injection vulnerability"
2. In Cursor: Select line
3. Cmd+K: "Fix this object injection vulnerability"

**AI Suggests:**
```javascript
// Fixed: Validate and sanitize input before assignment
const allowedFields = ['name', 'email', 'role'];
const sanitizedUpdates = {};

for (const [key, value] of Object.entries(updates)) {
  if (allowedFields.includes(key)) {
    sanitizedUpdates[key] = value;
  }
}

Object.assign(users[userIndex], sanitizedUpdates);
```

**AI Explanation:**
> "Object injection occurs when untrusted data is used to modify objects. An attacker could add or modify properties they shouldn't have access to. Whitelist allowed fields and only update those specific properties."

---

### Scenario 5: Fix Flaky Test

**Error Location:** `tests/users.test.js:67`

**Current Code:**
```javascript
test('flaky test - timing dependent', async () => {
  const startTime = Date.now();
  
  const response = await request(app)
    .get('/api/users/1')
    .expect(200);

  const duration = Date.now() - startTime;
  
  // This test fails if the response takes longer than 50ms (flaky timing)
  if (duration > 50) {
    throw new Error(`Test failed due to slow response: ${duration}ms`);
  }

  expect(response.body.user).toBeDefined();
});
```

**Steps:**
1. Run: `npm test` multiple times
2. See random failures
3. In Cursor: Open test file
4. Select flaky test
5. Cmd+K: "Fix this flaky test"

**AI Suggests:**
```javascript
test('reliable test - removed timing dependency', async () => {
  const response = await request(app)
    .get('/api/users/1')
    .expect(200);

  // Test the actual functionality, not timing
  expect(response.body.user).toBeDefined();
  expect(response.body.user.id).toBe(1);
  
  // If timing is important, use a reasonable timeout
  // and test it separately with proper retry logic
});
```

**AI Explanation:**
> "This test is flaky because it depends on response time, which varies based on system load. Tests should verify functionality, not performance. If you need to test performance, use dedicated performance tests with proper thresholds and retry logic."

---

## 🎯 Demo Script for Fix in Chat

### Setup (2 minutes)

```bash
# Ensure Cursor is open
# Ensure Datadog extension is enabled
# Ensure application is running
curl http://localhost:3000/api/health
```

### Demo Flow (10 minutes)

#### 1. Show Runtime Error Fix (3 min)

```bash
# Trigger error
curl http://localhost:3000/api/users/999
```

**Say:**
> "Let's see how Fix in Chat helps us resolve this production error..."

**Show:**
1. Error in Datadog Error Tracking
2. Click "Fix in Chat"
3. Cursor opens with context
4. AI suggests fix with explanation
5. Apply fix
6. Test: `curl http://localhost:3000/api/users/999`

---

#### 2. Show Security Vulnerability Fix (3 min)

```bash
# Run linter
npm run lint
```

**Say:**
> "Now let's fix this SQL injection vulnerability..."

**Show:**
1. ESLint detects SQL injection
2. Open file in Cursor
3. Select vulnerable line
4. Cmd+K: "Fix this SQL injection"
5. AI suggests parameterized query
6. Apply fix
7. Run lint again: `npm run lint`

---

#### 3. Show Flaky Test Fix (2 min)

```bash
# Run tests
npm test
npm test
npm test
```

**Say:**
> "This test sometimes passes, sometimes fails. Let's fix it..."

**Show:**
1. Open test file in Cursor
2. Select flaky test
3. Cmd+K: "Fix this flaky test"
4. AI explains timing issue
5. Suggests reliable alternative
6. Apply fix
7. Run tests: `npm test` (should pass consistently)

---

#### 4. Show Context-Aware Suggestions (2 min)

**Say:**
> "The AI understands your entire codebase and Datadog context..."

**Show:**
1. Open any file with issues
2. Ask: "What issues does Datadog see in this file?"
3. AI lists all issues with context
4. Ask: "Fix all issues"
5. AI provides comprehensive fixes

---

## 🔧 Advanced Usage

### Custom Prompts

```
# General fix
"Fix this error using Datadog context"

# Specific fix
"Fix this SQL injection vulnerability with parameterized queries"

# Explain first
"Explain this error and suggest a fix"

# Multiple fixes
"Fix all security vulnerabilities in this file"

# Best practices
"Fix this and apply best practices"

# With tests
"Fix this error and add tests"
```

### Batch Fixes

```
# Fix all linter errors
1. Run: npm run lint
2. In Cursor: Cmd+K
3. Ask: "Fix all ESLint errors in this project"
4. AI provides fixes for each file
```

### Integration with Datadog

```
# From Datadog dashboard
1. APM → Error Tracking
2. Filter by service: datadog-demo-app
3. Click any error
4. Click "Fix in Chat"
5. Cursor opens with full context
6. AI has access to:
   - Error stack trace
   - Request/response data
   - Environment state
   - Related logs
   - Similar errors
```

---

## ✅ Verification

### Test Fix in Chat is Working

1. **Check Cursor Extension:**
   - Open Cursor
   - Check Datadog extension is enabled
   - Verify connection to Datadog

2. **Test Error Context:**
   ```bash
   curl http://localhost:3000/api/users/999
   ```
   - Go to Datadog Error Tracking
   - Click error
   - Look for "Fix in Chat" button

3. **Test AI Suggestions:**
   - Open `src/app.js`
   - Select line with eval
   - Cmd+K: "Fix this"
   - Should get AI suggestion

4. **Test Linter Integration:**
   ```bash
   npm run lint
   ```
   - Open file with errors
   - Click on error
   - Should see fix suggestion

---

## 📊 Benefits

### For Developers

- ✅ **Faster fixes** - AI suggests solutions instantly
- ✅ **Learn best practices** - AI explains why
- ✅ **Context-aware** - Uses production error data
- ✅ **Consistent quality** - Applies standards automatically

### For Teams

- ✅ **Reduce MTTR** - Fix production issues faster
- ✅ **Improve code quality** - Catch issues early
- ✅ **Knowledge sharing** - AI teaches best practices
- ✅ **Reduce technical debt** - Fix issues systematically

### For Organizations

- ✅ **Faster development** - Less time debugging
- ✅ **Better security** - Automatic vulnerability fixes
- ✅ **Higher reliability** - Fix flaky tests
- ✅ **Lower costs** - Reduce incident response time

---

## 🚨 Important Notes

### What Fix in Chat Can Do

- ✅ Fix runtime errors
- ✅ Fix security vulnerabilities
- ✅ Fix flaky tests
- ✅ Suggest best practices
- ✅ Explain issues
- ✅ Provide context-aware solutions

### What Fix in Chat Cannot Do

- ❌ Fix architectural issues (needs human judgment)
- ❌ Make business logic decisions
- ❌ Replace code review
- ❌ Guarantee 100% correct fixes (always review)

### Best Practices

1. **Always review AI suggestions** before applying
2. **Test fixes** thoroughly
3. **Understand the explanation** - don't just copy/paste
4. **Use for learning** - AI teaches best practices
5. **Combine with code review** - AI + human is best

---

## 🎯 Success Metrics

After using Fix in Chat, you should see:

- ✅ Faster error resolution (50% reduction in MTTR)
- ✅ Fewer security vulnerabilities
- ✅ More reliable tests (fewer flaky tests)
- ✅ Better code quality
- ✅ Improved developer productivity

---

## 📚 Additional Resources

- **Cursor Docs:** https://cursor.sh/docs
- **Datadog Code Insights:** https://docs.datadoghq.com/code_insights/
- **Error Tracking:** https://docs.datadoghq.com/tracing/error_tracking/
- **Source Code Integration:** [SOURCE_CODE_INTEGRATION.md](SOURCE_CODE_INTEGRATION.md)

---

## 🔗 Related Features

- **Code Insights** - Detects issues automatically
- **View in IDE** - Jump to source code
- **Static Analysis** - Pre-commit checks
- **Exception Replay** - Full error context

All these features work together to provide a complete development experience!

---

**Questions?** Check the main [README.md](../README.md) or [FEATURES_CHECKLIST.md](FEATURES_CHECKLIST.md)

