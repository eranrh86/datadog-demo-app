# 🎬 Datadog Demo - Complete Step-by-Step Guide

**Repository:** https://github.com/eranrh86/datadog-demo-app  
**Service:** `datadog-demo-app`  
**Current Commit:** `c164a76`

---

## 📋 Pre-Demo Checklist

Before starting the demo, ensure you have:

- [ ] Datadog account with API key
- [ ] Docker installed (or Kubernetes cluster)
- [ ] Node.js 16+ installed
- [ ] Git repository cloned
- [ ] Terminal and browser ready
- [ ] Datadog UI open in browser

---

## 🚀 Part 1: Setup & Deployment (5-10 minutes)

### Step 1: Clone and Verify Repository

```bash
# Clone the repository
cd /path/to/datadog-demo-app

# Verify all features are configured
./verify-datadog-features.sh
```

**Expected Output:**
- ✅ Static Code Analysis configured
- ✅ Code Insights configured
- ✅ View in IDE configured
- ✅ Exception Replay configured

**What to Say:**
> "This is our demo application with all 4 Datadog developer features pre-configured. Let me show you the verification output..."

---

### Step 2: Build Docker Image with Git Metadata

```bash
# Build with Git metadata for source code integration
./build-with-git-metadata.sh
```

**Expected Output:**
```
📦 Git Repository: https://github.com/eranrh86/datadog-demo-app
📍 Commit SHA: c164a76...
🔨 Building Docker image with Git metadata...
✅ Docker image built successfully!
```

**What to Say:**
> "We're building the Docker image with Git metadata. This enables the 'View in IDE' feature, which allows you to jump from Datadog directly to the source code in GitHub."

**Key Point:** Show that the build includes `DD_GIT_REPOSITORY_URL` and `DD_GIT_COMMIT_SHA`

---

### Step 3: Deploy the Application

**Option A: Docker (Recommended for demo)**

```bash
# Set your Datadog API key
export DD_API_KEY=your_datadog_api_key_here

# Run the application
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

**Option B: Kubernetes**

```bash
# Update the commit SHA in deployment
sed -i '' "s/REPLACE_WITH_COMMIT_SHA/c164a76b7652633dfdd30b9c28638d0ae2d2fa79/" k8s/deployment.yaml

# Deploy
kubectl apply -f k8s/

# Get the service URL
kubectl get svc -n datadog-demo
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
> "The application is now running and sending data to Datadog. Let's give it a moment to start sending telemetry data..."

**Wait:** 30 seconds for data to start flowing

---

### Step 4: Generate Initial Traffic

```bash
# Generate some normal traffic
curl http://localhost:3000/
curl http://localhost:3000/api/users
curl http://localhost:3000/api/orders
curl http://localhost:3000/api/health/metrics
```

**What to Say:**
> "Let me generate some normal traffic first so we can see the baseline in Datadog..."

---

## 🎯 Part 2: Feature Demonstrations (20-25 minutes)

---

## 1️⃣ Static Code Analysis (3-5 minutes)

### Step 1: Show the Code

Open `src/app.js` in your editor and show lines 84-87:

```javascript
// VULNERABILITY: SQL Injection potential
const query = `SELECT * FROM users WHERE id = ${id}`;

// VULNERABILITY: Eval usage
const result = eval(`"User ID: ${id}"`);
```

**What to Say:**
> "This application intentionally has some security issues. Let's see how Datadog's static code analysis can detect them before we even commit the code."

---

### Step 2: Run Static Analysis

```bash
# Run ESLint with security plugin
npm run lint
```

**Expected Output:**
```
/path/to/datadog-demo-app/src/app.js
  91:18  error  eval with argument of type TemplateLiteral  security/detect-eval-with-expression
  91:18  error  eval can be harmful                         no-eval

/path/to/datadog-demo-app/src/routes/users.js
  146:17  error  Function Call Object Injection Sink       security/detect-object-injection
```

**What to Say:**
> "As you can see, ESLint immediately detected the eval usage and object injection vulnerabilities. This happens in your IDE before you even commit the code."

**Key Points:**
- ✅ Detects security issues pre-commit
- ✅ Integrated with IDE
- ✅ Prevents vulnerabilities from reaching production

---

### Step 3: Show in Datadog (if configured)

Navigate to: **Code Insights → Vulnerabilities**

**What to Say:**
> "These same issues also appear in Datadog's Code Insights dashboard, giving your security team visibility across all repositories."

---

## 2️⃣ Code Insights - Runtime Errors (5-7 minutes)

### Step 1: Trigger Runtime Errors

```bash
# Trigger null pointer exception
curl http://localhost:3000/api/users/999

# Trigger intentional error
curl http://localhost:3000/api/orders/666

# Trigger database error
curl http://localhost:3000/api/orders/500

# Trigger direct runtime error
curl http://localhost:3000/error/runtime
```

**Expected Output:**
```json
{
  "error": "Internal Server Error",
  "message": "Cannot read properties of null (reading 'profile')",
  "trace_id": "1234567890"
}
```

**What to Say:**
> "I'm triggering several different types of errors that might occur in production. Let's see how Datadog captures and presents these errors..."

---

### Step 2: View Errors in Datadog

1. **Navigate to:** APM → Error Tracking
2. **Filter by:** Service: `datadog-demo-app`
3. **Show the error list**

**What to Say:**
> "Here in Error Tracking, we can see all the errors that just occurred. Notice how they're automatically grouped by error type, and we can see the frequency, affected users, and more."

---

### Step 3: Drill into an Error

Click on the "Cannot read properties of null" error

**Show:**
- Error message and type
- Stack trace
- Number of occurrences
- Affected endpoints
- Error timeline

**What to Say:**
> "When we click into an error, we get the full stack trace, the exact line of code where it occurred, and we can see all the context around this error."

**Key Points:**
- ✅ Automatic error detection
- ✅ Grouped by error type
- ✅ Full stack traces
- ✅ No code changes required

---

### Step 4: Show Security Vulnerabilities

```bash
# Trigger SQL injection vulnerability
curl http://localhost:3000/vulnerable/123

# Attempt SQL injection
curl "http://localhost:3000/vulnerable/'; DROP TABLE users; --"
```

Navigate to: **Code Insights → Vulnerabilities**

**What to Say:**
> "Code Insights also shows us security vulnerabilities detected at runtime. This gives us defense-in-depth - catching issues both pre-commit and in production."

---

## 3️⃣ View in IDE - Source Code Integration (5-7 minutes)

### Step 1: Explain the Feature

**What to Say:**
> "One of the most powerful features is the ability to jump directly from an error in Datadog to the exact line of code in your IDE or GitHub. This is enabled by the Git metadata we included when building the Docker image."

---

### Step 2: Trigger an Error

```bash
# Trigger the null pointer error
curl http://localhost:3000/api/users/999
```

---

### Step 3: Navigate to Error in Datadog

1. **Go to:** APM → Error Tracking
2. **Click on:** "Cannot read properties of null" error
3. **Look for:** "View in IDE" or "View Code" button

**What to Say:**
> "See this 'View in IDE' button? This is the magic. When I click this..."

---

### Step 4: Click "View in IDE"

**Expected Behavior:**
- Opens GitHub to the exact file and line
- URL: `https://github.com/eranrh86/datadog-demo-app/blob/c164a76/src/routes/users.js#L48`
- Shows the exact line: `return res.json({ user: undefinedUser.profile.details });`

**What to Say:**
> "...it takes me directly to line 48 in users.js where the error occurred. This is the actual line of code that's running in production. No more hunting through files or guessing which version of the code is deployed."

**Key Points:**
- ✅ Jump from error to source code in one click
- ✅ Exact line and file
- ✅ Shows the deployed version of code
- ✅ Works with GitHub, GitLab, Bitbucket, Azure DevOps

---

### Step 5: Show Another Example

```bash
# Trigger runtime error
curl http://localhost:3000/error/runtime
```

Click "View in IDE" → Should open `src/app.js#L107`

**What to Say:**
> "This works for any error in your application. It's especially powerful when debugging production issues where you need to quickly understand what code is actually running."

---

## 4️⃣ Exception Replay - Production Debugging (5-7 minutes)

### Step 1: Explain the Feature

**What to Say:**
> "Exception Replay captures the complete context around an error - not just the stack trace, but the full request, response, environment state, and more. It's like having a DVR for your production errors."

---

### Step 2: Trigger Error with Context

```bash
# Create an order with invalid data
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -H "User-Agent: Demo-Client/1.0" \
  -H "X-Request-ID: demo-12345" \
  -d '{
    "userId": "invalid",
    "product": "Test Product",
    "amount": "not-a-number"
  }'

# Trigger user error
curl -H "X-User-ID: demo-user-123" \
     -H "X-Session-ID: session-abc" \
     http://localhost:3000/api/users/999

# Trigger order error
curl http://localhost:3000/api/orders/666
```

---

### Step 3: View in Datadog Error Tracking

1. **Go to:** APM → Error Tracking
2. **Click on:** Any of the errors you just triggered
3. **Show the "Overview" tab**

**What to Say:**
> "Let's look at what Exception Replay captures for us..."

---

### Step 4: Show Captured Context

**Navigate through the tabs and show:**

**Overview Tab:**
- Error message and type
- Stack trace with line numbers
- Error timeline

**Infrastructure Tab:**
- Host information
- Container details
- Memory usage
- CPU usage

**Logs Tab:**
- Correlated logs (thanks to log injection)
- Logs before and after the error
- Trace ID linking

**Network Tab (if available):**
- Request details
- Response details

**What to Say:**
> "Notice how we have the complete picture:
> - The full request including headers and body
> - The environment state at the time of the error
> - All related logs automatically correlated
> - The exact memory and CPU usage
> - Everything you need to reproduce and fix the issue"

---

### Step 5: Show Request Details

Click on the trace and show:

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
> "I can see exactly what the user sent in the request. This is invaluable for reproducing issues that only happen with specific input data."

**Key Points:**
- ✅ Full request/response capture
- ✅ Environment state at error time
- ✅ Automatic log correlation
- ✅ No code changes needed
- ✅ Privacy controls available

---

### Step 6: Show Health Check Errors

```bash
# Trigger health check failures (they fail randomly)
for i in {1..5}; do
  curl http://localhost:3000/api/health/ready
  sleep 1
done
```

Navigate to the health check errors in Datadog

**What to Say:**
> "Even for non-exception errors like health check failures, we capture the full context. You can see which dependency failed and why."

---

## 5️⃣ Bonus: Flaky Test Detection (3-5 minutes)

### Step 1: Explain the Feature

**What to Say:**
> "As a bonus, let me show you Datadog's flaky test detection. Flaky tests are tests that sometimes pass and sometimes fail with the same code - they're a huge pain for developers."

---

### Step 2: Run Tests Multiple Times

```bash
# Run tests 5 times
echo "Running tests 5 times to demonstrate flaky behavior..."
for i in {1..5}; do
  echo ""
  echo "=== Test Run #$i ==="
  npm test 2>&1 | tail -n 10
  sleep 2
done
```

**Expected Output:**
- Some runs will pass
- Some runs will fail (the flaky tests)
- Different results each time

**What to Say:**
> "Notice how the same tests sometimes pass and sometimes fail? These are flaky tests. They waste developer time and reduce confidence in your test suite."

---

### Step 3: Show in Datadog (if CI/CD configured)

Navigate to: **CI/CD → Test Visibility → Flaky Tests**

**What to Say:**
> "Datadog automatically detects these flaky tests and shows you which tests are unreliable. You can see the failure rate, when they started being flaky, and more."

**Key Points:**
- ✅ Automatic flaky test detection
- ✅ Shows failure patterns
- ✅ Helps prioritize test fixes
- ✅ Improves CI/CD reliability

---

## 🎯 Part 3: Putting It All Together (5 minutes)

### Step 1: Run Complete Demo Script

```bash
# This will demonstrate all features in sequence
./demo-all-features.sh
```

**What to Say:**
> "Let me run our comprehensive demo script that exercises all the features we just discussed..."

---

### Step 2: Show the Full Picture in Datadog

Navigate through Datadog to show:

1. **APM → Services → datadog-demo-app**
   - Service overview
   - Request rate, latency, errors
   - Dependencies

2. **APM → Error Tracking**
   - All errors grouped
   - Error trends
   - "View in IDE" buttons

3. **Code Insights**
   - Runtime errors
   - Vulnerabilities
   - Code quality issues

4. **Logs**
   - Correlated with traces
   - Filtered by service

**What to Say:**
> "This is the power of Datadog's unified platform. All your telemetry - traces, logs, errors, metrics - in one place, with deep integration into your development workflow."

---

### Step 3: Highlight Key Benefits

**What to Say:**
> "Let me summarize the key benefits we've seen today:
> 
> **1. Code Insights**
> - Catch errors and vulnerabilities early
> - No code changes required
> - Automatic detection
> 
> **2. View in IDE**
> - Jump from error to source code in one click
> - Always shows the deployed version
> - Works with any Git provider
> 
> **3. Static Code Analysis**
> - Detect issues before commit
> - Integrated with your IDE
> - Security-focused rules
> 
> **4. Exception Replay**
> - Full context for every error
> - Reproduce issues easily
> - Debug production problems faster
> 
> All of this works together to help developers ship code faster and with more confidence."

---

## 🧹 Part 4: Cleanup (2 minutes)

### Stop the Application

```bash
# Docker
docker stop datadog-demo-app
docker rm datadog-demo-app

# Kubernetes
kubectl delete -f k8s/
```

---

## 📊 Q&A Preparation

### Common Questions and Answers

**Q: Does this work with our existing code?**
> A: Yes! The only requirement is adding the Datadog tracer to your application. For "View in IDE", you just need to include Git metadata in your build process.

**Q: What about sensitive data in Exception Replay?**
> A: Datadog has extensive privacy controls. You can redact sensitive fields, exclude certain endpoints, and control what data is captured.

**Q: How much overhead does this add?**
> A: Minimal. The Datadog tracer is highly optimized and typically adds less than 1% overhead. You can also control sampling rates.

**Q: Does it work with microservices?**
> A: Absolutely! Datadog excels at distributed tracing across microservices. You'll see the full request flow across all services.

**Q: What languages are supported?**
> A: All major languages: Java, Python, Ruby, Go, Node.js, .NET, PHP, and more.

**Q: Can we try this with our own code?**
> A: Yes! I can help you set it up. The basic setup takes about 30 minutes.

---

## 🎯 Success Metrics

After the demo, the prospect should understand:

- ✅ How Code Insights detects runtime errors automatically
- ✅ How "View in IDE" saves time debugging
- ✅ How Static Code Analysis prevents issues
- ✅ How Exception Replay provides full error context
- ✅ The value of unified observability

---

## 📝 Follow-Up Actions

1. **Share the repository:**
   - https://github.com/eranrh86/datadog-demo-app

2. **Share documentation:**
   - Send QUICK_REFERENCE.md
   - Send FEATURES_CHECKLIST.md

3. **Offer POC:**
   - Help them set up with their own code
   - 30-day trial available

4. **Schedule follow-up:**
   - Technical deep dive
   - Architecture review
   - Pricing discussion

---

## 🚀 Quick Reference

### Key Commands

```bash
# Verify setup
./verify-datadog-features.sh

# Build with Git metadata
./build-with-git-metadata.sh

# Run complete demo
./demo-all-features.sh

# Trigger specific errors
curl http://localhost:3000/api/users/999      # Code Insights
curl http://localhost:3000/error/runtime      # View in IDE
curl http://localhost:3000/api/orders/666     # Exception Replay
npm run lint                                   # Static Analysis
npm test                                       # Flaky Tests
```

### Key URLs

- **GitHub:** https://github.com/eranrh86/datadog-demo-app
- **Datadog APM:** https://app.datadoghq.com/apm/services
- **Error Tracking:** https://app.datadoghq.com/apm/error-tracking
- **Code Insights:** https://app.datadoghq.com/ci/code-insights

---

## ✅ Pre-Demo Checklist (Print This!)

**Before the demo:**
- [ ] Application built with Git metadata
- [ ] Application deployed and running
- [ ] Datadog UI open in browser
- [ ] Terminal ready with commands
- [ ] Repository open in IDE
- [ ] Tested all endpoints work
- [ ] Data flowing to Datadog (wait 30s after deploy)

**During the demo:**
- [ ] Explain each feature before demonstrating
- [ ] Show the code first, then the Datadog UI
- [ ] Highlight the "View in IDE" button
- [ ] Show full context in Exception Replay
- [ ] Emphasize "no code changes required"

**After the demo:**
- [ ] Answer questions
- [ ] Share repository link
- [ ] Offer POC/trial
- [ ] Schedule follow-up

---

**Good luck with your demo! 🎉**

For questions or issues, check:
- STATUS.md - Current status
- QUICK_REFERENCE.md - Quick commands
- docs/FEATURES_CHECKLIST.md - Detailed checklist

