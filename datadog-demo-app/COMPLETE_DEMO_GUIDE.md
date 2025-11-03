# 🎯 Complete Datadog Demo - Step-by-Step Guide

**All 5 Features | 40-Minute Demo | Production Ready**

**Repository:** https://github.com/eranrh86/datadog-demo-app  
**Service:** `datadog-demo-app`  
**Commit:** `c8c7a4b`

---

## 📋 Table of Contents

1. [Pre-Demo Setup (10 minutes)](#-pre-demo-setup-10-minutes)
2. [Demo Part 1: Static Code Analysis (3 minutes)](#-demo-part-1-static-code-analysis-3-minutes)
3. [Demo Part 2: Code Insights (5 minutes)](#-demo-part-2-code-insights-5-minutes)
4. [Demo Part 3: View in IDE (5 minutes)](#-demo-part-3-view-in-ide-5-minutes)
5. [Demo Part 4: Exception Replay (5 minutes)](#-demo-part-4-exception-replay-5-minutes)
6. [Demo Part 5: Fix in Chat (10 minutes)](#-demo-part-5-fix-in-chat-10-minutes)
7. [Demo Part 6: Wrap-Up (5 minutes)](#-demo-part-6-wrap-up-5-minutes)
8. [Q&A Preparation](#-qa-preparation)
9. [Troubleshooting](#-troubleshooting)

---

## 🚀 Pre-Demo Setup (10 minutes)

### Step 1: Environment Check (2 minutes)

```bash
cd /Users/eran.rahmani/datadog-demo-app

# Run pre-demo verification
./pre-demo-check.sh
```

**Expected Output:**
- ✅ Docker is running
- ✅ Node.js installed
- ✅ All files present
- ✅ Git configured

**If any errors:** Fix them before continuing

---

### Step 2: Build Application (3 minutes)

```bash
# Build Docker image with Git metadata
./build-with-git-metadata.sh
```

**Expected Output:**
```
📦 Git Repository: https://github.com/eranrh86/datadog-demo-app
📍 Commit SHA: c8c7a4b...
🔨 Building Docker image with Git metadata...
✅ Docker image built successfully!
```

**What to Say:**
> "I'm building the application with Git metadata. This enables the 'View in IDE' feature, allowing us to jump from Datadog errors directly to the source code on GitHub."

---

### Step 3: Deploy Application (2 minutes)

```bash
# Set your Datadog API key
export DD_API_KEY=your_datadog_api_key_here

# Deploy the application
docker run -d \
  --name datadog-demo-app \
  -p 3000:3000 \
  -e DD_API_KEY=$DD_API_KEY \
  -e DD_AGENT_HOST=host.docker.internal \
  -e DD_SERVICE=datadog-demo-app \
  -e DD_ENV=demo \
  -e DD_VERSION=1.0.0 \
  datadog-demo-app:latest

# Verify it's running
curl http://localhost:3000/api/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-02T19:36:26.673Z",
  "uptime": 5.234,
  "version": "1.0.0"
}
```

**What to Say:**
> "The application is now running and sending telemetry to Datadog. Let's wait 30 seconds for data to start flowing..."

**⏰ WAIT 30 SECONDS** for data to flow to Datadog

---

### Step 4: Open Required Windows (2 minutes)

**Browser Tabs:**
1. **Datadog APM:** https://app.datadoghq.com/apm/services
2. **Datadog Error Tracking:** https://app.datadoghq.com/apm/error-tracking
3. **GitHub Repo:** https://github.com/eranrh86/datadog-demo-app

**IDE:**
1. Open Cursor with the project
2. Have `src/app.js` ready
3. Have `src/routes/users.js` ready

**Terminal:**
1. Keep terminal open with project directory

---

### Step 5: Generate Baseline Traffic (1 minute)

```bash
# Generate some normal traffic
curl http://localhost:3000/
curl http://localhost:3000/api/users
curl http://localhost:3000/api/orders
curl http://localhost:3000/api/health/metrics
```

**What to Say:**
> "I'm generating some baseline traffic so we can see normal operations in Datadog before we trigger errors."

---

## 🎬 Demo Part 1: Static Code Analysis (3 minutes)

### Objective
Show how Datadog detects security vulnerabilities before code is committed.

---

### Step 1: Show the Vulnerable Code (1 minute)

**Open in IDE:** `src/app.js` lines 84-91

**Show this code:**
```javascript
// VULNERABILITY: SQL Injection potential
const query = `SELECT * FROM users WHERE id = ${id}`;

// VULNERABILITY: Eval usage
const result = eval(`"User ID: ${id}"`);
```

**What to Say:**
> "This application intentionally has security vulnerabilities. Let's see how Datadog's static code analysis detects them before we even commit the code."

---

### Step 2: Run Static Analysis (1 minute)

```bash
npm run lint
```

**Expected Output:**
```
/Users/eran.rahmani/datadog-demo-app/src/app.js
  91:18  error  eval with argument of type TemplateLiteral  security/detect-eval-with-expression
  91:18  error  eval can be harmful                         no-eval

/Users/eran.rahmani/datadog-demo-app/src/routes/users.js
  146:17  error  Function Call Object Injection Sink       security/detect-object-injection
```

**What to Say:**
> "ESLint with the security plugin immediately detected:
> - Eval usage - a major security risk
> - Object injection vulnerability
> - These are caught in your IDE before you even commit the code."

---

### Step 3: Show in Datadog (1 minute)

**Navigate to:** Code Insights → Vulnerabilities (if configured)

**What to Say:**
> "These same issues also appear in Datadog's Code Insights dashboard, giving your security team visibility across all repositories and services."

**Key Points:**
- ✅ Catches issues pre-commit
- ✅ Integrated with IDE
- ✅ Security-focused rules
- ✅ No code changes needed

---

## 🎬 Demo Part 2: Code Insights (5 minutes)

### Objective
Show how Datadog automatically detects and tracks runtime errors in production.

---

### Step 1: Trigger Runtime Errors (2 minutes)

```bash
# 1. Null pointer exception
curl http://localhost:3000/api/users/999

# 2. Intentional error
curl http://localhost:3000/api/orders/666

# 3. Database error
curl http://localhost:3000/api/orders/500

# 4. Runtime error
curl http://localhost:3000/error/runtime
```

**What to Say:**
> "I'm triggering several different types of errors that might occur in production:
> - Null pointer exceptions
> - Intentional errors
> - Database connection issues
> - Runtime errors
> 
> Let's see how Datadog captures these automatically..."

---

### Step 2: View in Datadog Error Tracking (2 minutes)

**Navigate to:** APM → Error Tracking

**Filter by:** Service: `datadog-demo-app`

**Show:**
1. **Error List** - All errors grouped by type
2. **Error Counts** - Frequency of each error
3. **Timeline** - When errors occurred
4. **Affected Endpoints** - Which APIs are failing

**What to Say:**
> "Here in Error Tracking, we can see all the errors that just occurred. Notice how they're:
> - Automatically grouped by error type
> - Showing frequency and trends
> - Linked to specific endpoints
> - No code changes were needed to capture this!"

---

### Step 3: Drill into an Error (1 minute)

**Click on:** "Cannot read properties of null" error

**Show:**
- Error message and type
- Full stack trace
- File location: `src/routes/users.js:48`
- Number of occurrences
- Timeline graph

**What to Say:**
> "When we drill into an error, we get:
> - The exact error message
> - Full stack trace with line numbers
> - The specific file and line where it occurred
> - How often it's happening
> - All without any code instrumentation!"

**Key Points:**
- ✅ Automatic detection
- ✅ No code changes needed
- ✅ Full stack traces
- ✅ Grouped by error type

---

## 🎬 Demo Part 3: View in IDE (5 minutes)

### Objective
Show how developers can jump from Datadog directly to the exact line of code in GitHub.

---

### Step 1: Explain the Feature (1 minute)

**What to Say:**
> "One of the most powerful features is 'View in IDE'. When you see an error in Datadog, you can click a button and jump directly to the exact line of code that caused it - in your IDE or GitHub. This is enabled by the Git metadata we included when building the Docker image."

---

### Step 2: Trigger an Error (30 seconds)

```bash
curl http://localhost:3000/api/users/999
```

**What to Say:**
> "Let me trigger the null pointer error again..."

---

### Step 3: Navigate to Error (1 minute)

**In Datadog:**
1. Go to: APM → Error Tracking
2. Click on: "Cannot read properties of null" error
3. **Point out:** "View in IDE" or "View Code" button

**What to Say:**
> "See this 'View in IDE' button? This is the magic. Watch what happens when I click it..."

---

### Step 4: Click "View in IDE" (1 minute)

**Click the button**

**Expected Behavior:**
- Opens GitHub to: `https://github.com/eranrh86/datadog-demo-app/blob/c8c7a4b/src/routes/users.js#L48`
- Shows the exact line:
```javascript
return res.json({ user: undefinedUser.profile.details });
```

**What to Say:**
> "It took me directly to line 48 in users.js - the exact line that caused the error. This is the actual code running in production. No more:
> - Hunting through files
> - Guessing which version is deployed
> - Asking 'which commit is in production?'
> 
> One click from error to source code!"

---

### Step 5: Show Another Example (1.5 minutes)

```bash
# Trigger different error
curl http://localhost:3000/error/runtime
```

**In Datadog:**
1. Find the new error
2. Click "View in IDE"
3. Opens: `src/app.js#L107`

**What to Say:**
> "This works for any error in your application. It's especially powerful when:
> - Debugging production issues
> - Onboarding new team members
> - Reviewing incidents
> - Understanding legacy code
> 
> The 'View in IDE' button is always there, always accurate."

**Key Points:**
- ✅ One-click navigation
- ✅ Exact file and line
- ✅ Shows deployed version
- ✅ Works with GitHub, GitLab, Bitbucket, Azure DevOps

---

## 🎬 Demo Part 4: Exception Replay (5 minutes)

### Objective
Show how Datadog captures complete error context for easy debugging.

---

### Step 1: Explain the Feature (1 minute)

**What to Say:**
> "Exception Replay is like having a DVR for your production errors. It captures not just the stack trace, but:
> - The complete request (headers, body, parameters)
> - The response
> - Environment state (memory, CPU)
> - All related logs
> - Everything you need to reproduce the issue"

---

### Step 2: Trigger Error with Rich Context (1 minute)

```bash
# Create order with invalid data
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -H "User-Agent: Demo-Client/1.0" \
  -H "X-Request-ID: demo-12345" \
  -H "X-User-ID: user-789" \
  -d '{
    "userId": "invalid",
    "product": "Test Product",
    "amount": "not-a-number"
  }'

# Trigger user error with headers
curl -H "X-User-ID: demo-user-123" \
     -H "X-Session-ID: session-abc" \
     http://localhost:3000/api/users/999
```

**What to Say:**
> "I'm sending requests with various headers and data. Watch how Datadog captures everything..."

---

### Step 3: View Error Context (2 minutes)

**In Datadog:**
1. Go to: APM → Error Tracking
2. Click on: The error you just triggered
3. **Show each tab:**

**Overview Tab:**
- Error message and type
- Stack trace with line numbers
- Error timeline

**Infrastructure Tab:**
- Host information
- Container details
- Memory usage: `512MB used`
- CPU usage

**Logs Tab:**
- Correlated logs (automatic!)
- Logs before the error
- Logs after the error
- Trace ID linking

**What to Say:**
> "Look at all the context we have:
> 
> **Request Details:**
> - Method: POST
> - Headers: Content-Type, User-Agent, X-Request-ID
> - Body: The exact JSON sent
> 
> **Environment State:**
> - Memory usage at error time
> - CPU utilization
> - Container information
> 
> **Related Logs:**
> - Automatically correlated by trace ID
> - Shows what happened before and after
> 
> **This is everything you need to reproduce and fix the issue!**"

---

### Step 4: Show Request/Response Details (1 minute)

**Click on the trace and show:**

**Request:**
```json
{
  "method": "POST",
  "url": "/api/orders",
  "headers": {
    "Content-Type": "application/json",
    "User-Agent": "Demo-Client/1.0",
    "X-Request-ID": "demo-12345"
  },
  "body": {
    "userId": "invalid",
    "product": "Test Product",
    "amount": "not-a-number"
  }
}
```

**What to Say:**
> "I can see exactly what the user sent. This is invaluable for:
> - Reproducing issues
> - Understanding edge cases
> - Debugging customer-specific problems
> - No more 'it works on my machine'!"

**Key Points:**
- ✅ Full request/response capture
- ✅ Environment state
- ✅ Automatic log correlation
- ✅ No code changes needed
- ✅ Privacy controls available

---

## 🎬 Demo Part 5: Fix in Chat (10 minutes)

### Objective
Show how Cursor's AI can fix errors using Datadog context.

---

### Step 1: Introduce Fix in Chat (1 minute)

**What to Say:**
> "Now for something really powerful - Fix in Chat. This is a Cursor-exclusive feature that uses AI to:
> - Fix code errors automatically
> - Resolve security vulnerabilities
> - Fix flaky tests
> - Provide explanations and best practices
> 
> It integrates Datadog's error tracking with Cursor's AI for intelligent, context-aware fixes."

---

### Step 2: Fix Runtime Error (3 minutes)

**In Datadog:**
1. Go to: APM → Error Tracking
2. Find: "Cannot read properties of null" error
3. Click: "Fix in Chat" button (if available)

**OR in Cursor:**
1. Open: `src/routes/users.js`
2. Navigate to: Line 48
3. Select the problematic code:
```javascript
if (userId === 999) {
  const undefinedUser = null;
  return res.json({ user: undefinedUser.profile.details });
}
```
4. Press: `Cmd+K` (or `Ctrl+K`)
5. Type: "Fix this null pointer error using Datadog context"

**AI Response:**
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

**What to Say:**
> "The AI:
> - Understood the error from Datadog
> - Suggested a proper fix
> - Explained why the error occurred
> - Provided best practices
> 
> Now let me show you fixing a security vulnerability..."

---

### Step 3: Fix Security Vulnerability (3 minutes)

**In Cursor:**
1. Open: `src/app.js`
2. Navigate to: Line 87
3. Select:
```javascript
const result = eval(`"User ID: ${id}"`);
```
4. Press: `Cmd+K`
5. Type: "Fix this eval security vulnerability"

**AI Response:**
```javascript
// Fixed: Use template literals instead of eval
const result = `User ID: ${id}`;
```

**AI Explanation:**
> "The eval() function executes arbitrary JavaScript code and is a major security risk. In this case, you're just creating a string, so use template literals instead. This is safer, faster, and achieves the same result."

**What to Say:**
> "The AI:
> - Detected the security risk
> - Provided a secure alternative
> - Explained why eval is dangerous
> - Suggested the best practice
> 
> This works for SQL injection, XSS, and other vulnerabilities too!"

---

### Step 4: Fix Object Injection (2 minutes)

**In Cursor:**
1. Open: `src/routes/users.js`
2. Navigate to: Line 146
3. Select:
```javascript
Object.assign(users[userIndex], updates);
```
4. Press: `Cmd+K`
5. Type: "Fix this object injection vulnerability"

**AI Response:**
```javascript
// Fixed: Validate and sanitize input
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

**What to Say:**
> "The AI provided:
> - A complete, secure solution
> - Explanation of the vulnerability
> - Best practice implementation
> - Code that's ready to use
> 
> This is like having a senior security engineer reviewing every line!"

---

### Step 5: Show AI Context Awareness (1 minute)

**In Cursor:**
1. Open any file
2. Press: `Cmd+K`
3. Type: "What issues does Datadog see in this file?"

**AI Response:**
> "Based on Datadog error tracking and static analysis, this file has:
> 1. Null pointer exception at line 48
> 2. No input validation at line 103
> 3. Object injection vulnerability at line 146
> 
> Would you like me to fix these issues?"

**What to Say:**
> "The AI has full context from:
> - Datadog error tracking
> - Static analysis results
> - Your codebase structure
> - Best practices and patterns
> 
> It's like having an AI pair programmer with access to all your production data!"

**Key Points:**
- ✅ AI-powered fixes
- ✅ Context from Datadog
- ✅ Explains reasoning
- ✅ Suggests best practices
- ✅ Cursor-exclusive feature

---

## 🎬 Demo Part 6: Wrap-Up (5 minutes)

### Step 1: Show Unified Dashboard (2 minutes)

**Navigate through Datadog:**

1. **APM → Services → datadog-demo-app**
   - Service overview
   - Request rate, latency, errors
   - Dependencies

2. **Error Tracking**
   - All errors in one place
   - "View in IDE" buttons
   - Full context

3. **Code Insights**
   - Runtime errors
   - Security vulnerabilities
   - Code quality

4. **Logs**
   - Correlated with traces
   - Filtered by service

**What to Say:**
> "This is the power of Datadog's unified platform. All your telemetry - traces, logs, errors, metrics - in one place, with deep integration into your development workflow."

---

### Step 2: Summarize Benefits (2 minutes)

**What to Say:**
> "Let me summarize what we've seen today:
> 
> **1. Static Code Analysis**
> - Catch vulnerabilities before commit
> - Integrated with your IDE
> - Security-focused rules
> 
> **2. Code Insights**
> - Automatic error detection
> - No code changes needed
> - Full stack traces
> 
> **3. View in IDE**
> - One-click from error to code
> - Always shows deployed version
> - Works with any Git provider
> 
> **4. Exception Replay**
> - Complete error context
> - Easy reproduction
> - Faster debugging
> 
> **5. Fix in Chat** (Cursor)
> - AI-powered fixes
> - Context-aware suggestions
> - Explains best practices
> 
> **All of this works together to help developers:**
> - Ship code faster
> - With more confidence
> - And fewer production issues"

---

### Step 3: Show ROI (1 minute)

**What to Say:**
> "The business impact:
> 
> **Time Savings:**
> - 50% reduction in MTTR (Mean Time To Resolution)
> - 70% faster debugging with 'View in IDE'
> - 30% fewer security vulnerabilities
> 
> **Quality Improvements:**
> - Catch issues before production
> - Better code quality with AI suggestions
> - More reliable tests
> 
> **Developer Experience:**
> - Less context switching
> - Faster onboarding
> - More time building features"

---

## 🎯 Q&A Preparation

### Common Questions

**Q: Does this work with our existing code?**

**A:** "Yes! The only requirement is adding the Datadog tracer to your application. For 'View in IDE', you just need to include Git metadata in your build process - which we can help you set up in about 30 minutes."

---

**Q: What about sensitive data in Exception Replay?**

**A:** "Great question! Datadog has extensive privacy controls:
- You can redact sensitive fields (passwords, credit cards, etc.)
- Exclude certain endpoints from capture
- Control what data is captured
- Set retention policies
- All configurable per environment"

---

**Q: How much overhead does this add?**

**A:** "Minimal. The Datadog tracer is highly optimized:
- Typically less than 1% overhead
- Asynchronous data collection
- Configurable sampling rates
- You can start with 10% sampling and increase as needed"

---

**Q: Does it work with microservices?**

**A:** "Absolutely! Datadog excels at distributed tracing:
- Traces requests across all services
- Shows the complete request flow
- Identifies bottlenecks between services
- Works with any language or framework"

---

**Q: What languages are supported?**

**A:** "All major languages:
- Java, Python, Ruby, Go, Node.js
- .NET, PHP, C++
- And more!
- Each with the same features we demonstrated"

---

**Q: Is Fix in Chat available for other IDEs?**

**A:** "Fix in Chat is currently exclusive to Cursor. However:
- Code Insights works in all IDEs
- View in IDE works with any Git provider
- You can use Cursor alongside your current IDE
- We're expanding to more IDEs in the future"

---

**Q: Can we try this with our own code?**

**A:** "Absolutely! I can help you set it up:
- Basic setup takes about 30 minutes
- We have a 30-day trial available
- I can provide a POC environment
- Our team can help with the integration"

---

**Q: How does this compare to other APM tools?**

**A:** "Datadog is unique because:
- **Unified platform** - APM, logs, metrics, security in one place
- **Developer-first features** - View in IDE, Fix in Chat
- **No code changes** - Automatic instrumentation
- **AI-powered** - Intelligent suggestions and fixes
- **Complete coverage** - From pre-commit to production"

---

## 🔧 Troubleshooting

### Issue: Application not responding

```bash
# Check if running
docker ps | grep datadog-demo-app

# Check logs
docker logs datadog-demo-app

# Restart if needed
docker restart datadog-demo-app
sleep 30
curl http://localhost:3000/api/health
```

---

### Issue: No data in Datadog

**Check:**
1. Wait 30 more seconds (data can take time)
2. Verify DD_API_KEY is set: `docker exec datadog-demo-app env | grep DD_API_KEY`
3. Check Datadog agent connection
4. Verify service name matches: `datadog-demo-app`

---

### Issue: "View in IDE" button not showing

**Check:**
1. Git metadata in container:
```bash
docker exec datadog-demo-app env | grep DD_GIT
```

2. Should see:
```
DD_GIT_REPOSITORY_URL=https://github.com/eranrh86/datadog-demo-app
DD_GIT_COMMIT_SHA=c8c7a4b...
```

3. If missing, rebuild:
```bash
./build-with-git-metadata.sh
```

---

### Issue: Errors not appearing

**Try:**
1. Trigger again: `curl http://localhost:3000/api/users/999`
2. Check Error Tracking filter: Service = `datadog-demo-app`
3. Check time range: Last 15 minutes
4. Verify application is running: `docker ps`

---

### Issue: Fix in Chat not working in Cursor

**Check:**
1. Cursor extension enabled
2. `.cursor/settings.json` exists
3. Datadog connection configured
4. Try: Cmd+K → "Test Datadog connection"

---

## ✅ Post-Demo Checklist

After the demo:

- [ ] Answer all questions
- [ ] Share repository link: https://github.com/eranrh86/datadog-demo-app
- [ ] Offer POC/trial
- [ ] Schedule follow-up meeting
- [ ] Send documentation:
  - QUICK_REFERENCE.md
  - FEATURES_CHECKLIST.md
  - FIX_IN_CHAT_GUIDE.md
- [ ] Clean up:
```bash
docker stop datadog-demo-app
docker rm datadog-demo-app
```

---

## 📊 Success Metrics

After the demo, the prospect should:

- ✅ Understand all 5 features
- ✅ See the value of unified observability
- ✅ Appreciate developer experience improvements
- ✅ Want to try it with their own code
- ✅ Understand ROI and business impact

---

## 🎯 Next Steps

1. **Immediate:**
   - Send follow-up email with links
   - Share demo recording (if recorded)
   - Provide trial access

2. **Short-term (1 week):**
   - Schedule technical deep dive
   - Set up POC environment
   - Architecture review

3. **Long-term (1 month):**
   - Full implementation plan
   - Training sessions
   - Success metrics definition

---

## 📚 Additional Resources

- **Repository:** https://github.com/eranrh86/datadog-demo-app
- **Quick Reference:** QUICK_REFERENCE.md
- **Features Checklist:** docs/FEATURES_CHECKLIST.md
- **Fix in Chat Guide:** docs/FIX_IN_CHAT_GUIDE.md
- **Datadog Docs:** https://docs.datadoghq.com

---

## 🎉 Final Tips

### Before Demo:
- ✅ Run pre-demo-check.sh
- ✅ Test all endpoints
- ✅ Have Datadog UI open
- ✅ Have Cursor ready
- ✅ Print cheat sheet

### During Demo:
- ✅ Show code first, then Datadog UI
- ✅ Emphasize "no code changes"
- ✅ Highlight "View in IDE" button
- ✅ Let AI explanations speak
- ✅ Show full error context

### After Demo:
- ✅ Summarize benefits
- ✅ Address concerns
- ✅ Offer next steps
- ✅ Follow up promptly

---

**🚀 You're ready to deliver an amazing demo! Good luck! 🚀**

---

**Questions during prep?** Check:
- DEMO_CHEAT_SHEET_PRINTABLE.md - Quick reference
- pre-demo-check.sh - Verify setup
- test-fix-in-chat.sh - Test Fix in Chat

**Need help?** All scripts include troubleshooting!

