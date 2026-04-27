# ✅ Datadog Features Checklist

Complete verification checklist for all 4 key Datadog developer features.

**Repository:** https://github.com/eranrh86/datadog-demo-app  
**Service:** `datadog-demo-app`

---

## 🎯 Quick Verification

Run the verification script to check all features:

```bash
./verify-datadog-features.sh
```

Run the complete demo:

```bash
./demo-all-features.sh
```

---

## 1️⃣ Code Insights

**Purpose:** Stay informed about runtime errors, vulnerabilities, and flaky tests without leaving the code.

### ✅ Configuration Checklist

- [x] **Datadog tracer initialized** in `src/app.js`
- [x] **Error tracking enabled** with proper error handlers
- [x] **Runtime errors** intentionally added for demo
- [x] **Security vulnerabilities** intentionally added for demo
- [x] **ESLint security plugin** configured

### 📍 Runtime Error Endpoints

| Endpoint | Error Type | File Location |
|----------|-----------|---------------|
| `GET /api/users/999` | Null pointer exception | `src/routes/users.js:48` |
| `GET /api/orders/666` | Intentional error | `src/routes/orders.js:66` |
| `GET /api/orders/500` | Database error | `src/routes/orders.js:82` |
| `GET /error/runtime` | Runtime error | `src/app.js:107` |
| `GET /api/health/ready` | Health check failures | `src/routes/health.js:51-58` |

### 🔒 Security Vulnerabilities

| Endpoint | Vulnerability | File Location |
|----------|--------------|---------------|
| `GET /vulnerable/:id` | SQL injection | `src/app.js:84` |
| `GET /vulnerable/:id` | Eval usage | `src/app.js:87` |
| `POST /api/users` | No email validation | `src/routes/users.js:103` |
| `PUT /api/users/:id` | No input sanitization | `src/routes/users.js:146` |

### 🧪 Test It

```bash
# Trigger runtime errors
curl http://localhost:3000/api/users/999
curl http://localhost:3000/api/orders/666
curl http://localhost:3000/error/runtime

# Trigger security vulnerabilities
curl http://localhost:3000/vulnerable/123
curl "http://localhost:3000/vulnerable/'; DROP TABLE users; --"
```

### 📊 View in Datadog

1. Go to **APM → Error Tracking**
2. See runtime errors with full context
3. Go to **Code Insights → Vulnerabilities**
4. See security issues detected

---

## 2️⃣ View in IDE

**Purpose:** Jump directly from code references in Datadog to your source files.

### ✅ Configuration Checklist

- [x] **Git metadata in Dockerfile** (`DD_GIT_REPOSITORY_URL`, `DD_GIT_COMMIT_SHA`)
- [x] **Git metadata in app.js** (environment variables set)
- [x] **Git metadata in K8s deployment** (environment variables)
- [x] **dd-trace version 3.21.0+** (currently 4.20.0)
- [x] **Source maps enabled** (`--enable-source-maps` flag)
- [x] **Build script created** (`build-with-git-metadata.sh`)

### 🔧 Setup

```bash
# Build Docker image with Git metadata
./build-with-git-metadata.sh

# Or manually
docker build . \
  -t datadog-demo-app:latest \
  --build-arg DD_GIT_REPOSITORY_URL=https://github.com/eranrh86/datadog-demo-app \
  --build-arg DD_GIT_COMMIT_SHA=$(git rev-parse HEAD)
```

### 🧪 Test It

```bash
# Generate errors
curl http://localhost:3000/api/users/999
curl http://localhost:3000/error/runtime

# In Datadog:
# 1. Go to APM → Error Tracking
# 2. Click on any error
# 3. Click "View in IDE" button
# 4. Should open exact file and line in your IDE!
```

### 📊 View in Datadog

1. Go to **APM → Error Tracking**
2. Click any error trace
3. Look for **"View in IDE"** button
4. Click to jump to source code

### 🔍 Verification

Check that Git metadata is set:

```bash
# In Docker
docker exec <container-id> env | grep DD_GIT

# In Kubernetes
kubectl exec -it <pod-name> -n datadog-demo -- env | grep DD_GIT
```

Should see:
```
DD_GIT_REPOSITORY_URL=https://github.com/eranrh86/datadog-demo-app
DD_GIT_COMMIT_SHA=<your-commit-sha>
```

---

## 3️⃣ Static Code Analysis

**Purpose:** Detect and fix problems before you commit changes.

### ✅ Configuration Checklist

- [x] **ESLint configured** (`.eslintrc.js`)
- [x] **Security plugin enabled** (`eslint-plugin-security`)
- [x] **npm script configured** (`npm run lint`)
- [x] **Security rules enabled** (SQL injection, eval, object injection)
- [x] **Snyk configured** for vulnerability scanning

### 🔧 Setup

ESLint is configured with security rules in `.eslintrc.js`:

```javascript
plugins: ['security'],
rules: {
  'security/detect-sql-injection': 'error',
  'security/detect-eval-with-expression': 'error',
  'security/detect-object-injection': 'error',
  // ... more rules
}
```

### 🧪 Test It

```bash
# Run linting
npm run lint

# Run security scan
npm run security-scan

# Or both
npm audit && npm run lint
```

### 📊 Expected Output

ESLint will detect:
- ✗ SQL injection in `src/app.js:84`
- ✗ Eval usage in `src/app.js:87`
- ✗ Object injection in `src/routes/users.js:146`

### 📊 View in Datadog

1. Go to **Code Insights → Vulnerabilities**
2. See detected security issues
3. See code quality problems
4. Get recommendations for fixes

---

## 4️⃣ Exception Replay

**Purpose:** Debug your production code with full error context.

### ✅ Configuration Checklist

- [x] **Error handler middleware** (`src/middleware/errorHandler.js`)
- [x] **Log injection enabled** (`logInjection: true`)
- [x] **Trace correlation** (logs linked to traces)
- [x] **Error tags on spans** (error.type, error.message, error.stack)
- [x] **Request/response capture** in error handler
- [x] **Environment state capture**

### 🔧 Configuration

Error handler captures:
- Full stack traces
- Request details (headers, body, params, query)
- Response details
- User session information
- Environment variables
- System state (memory, uptime)

### 🧪 Test It

```bash
# Generate errors with full context
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"userId":"invalid","product":"Test","amount":"not-a-number"}'

curl http://localhost:3000/api/users/999
curl http://localhost:3000/api/orders/666
```

### 📊 View in Datadog

1. Go to **APM → Error Tracking**
2. Click any error
3. See **full request details**:
   - Headers
   - Body
   - Query parameters
   - URL parameters
4. See **full response details**
5. See **environment state**:
   - Memory usage
   - Uptime
   - Node version
6. See **complete stack trace** with source code

---

## 5️⃣ Bonus: Flaky Test Detection

**Purpose:** Identify unreliable tests automatically.

### ✅ Configuration Checklist

- [x] **Jest configured** (`jest.config.js`)
- [x] **Flaky tests added** (`tests/users.test.js`)
- [x] **npm script configured** (`npm run test:flaky`)
- [x] **Tests fail randomly** (~30% failure rate)

### 🧪 Test It

```bash
# Run tests multiple times
npm test
npm test
npm test

# Or run just flaky tests
npm run test:flaky
npm run test:flaky
npm run test:flaky
```

### 📊 View in Datadog

1. Go to **CI/CD → Test Visibility**
2. See **Flaky Tests** section
3. See tests that fail randomly
4. See failure patterns and trends

---

## 🎯 Complete Demo Flow

### Step 1: Verify Configuration

```bash
./verify-datadog-features.sh
```

### Step 2: Build with Git Metadata

```bash
./build-with-git-metadata.sh
```

### Step 3: Deploy Application

```bash
# Docker
docker run -d -p 3000:3000 \
  -e DD_API_KEY=$DD_API_KEY \
  -e DD_AGENT_HOST=host.docker.internal \
  datadog-demo-app:latest

# Or Kubernetes
kubectl apply -f k8s/
```

### Step 4: Run Complete Demo

```bash
./demo-all-features.sh
```

### Step 5: View in Datadog

1. **Code Insights**
   - APM → Error Tracking → See runtime errors
   - Code Insights → Vulnerabilities

2. **View in IDE**
   - APM → Error Tracking → Click error → "View in IDE"

3. **Static Code Analysis**
   - Code Insights → Vulnerabilities
   - See ESLint findings

4. **Exception Replay**
   - APM → Error Tracking → Click error
   - See full request/response context

5. **Flaky Tests**
   - CI/CD → Test Visibility → Flaky Tests

---

## 📝 Summary

### All Features Configured ✅

| Feature | Status | Demo Endpoint | Datadog Location |
|---------|--------|---------------|------------------|
| Code Insights | ✅ | `/api/users/999` | APM → Error Tracking |
| View in IDE | ✅ | `/error/runtime` | Error → "View in IDE" |
| Static Analysis | ✅ | `npm run lint` | Code Insights → Vulnerabilities |
| Exception Replay | ✅ | `/api/orders/666` | APM → Error Tracking → Details |
| Flaky Tests | ✅ | `npm test` | CI/CD → Test Visibility |

### Repository Details

- **GitHub:** https://github.com/eranrh86/datadog-demo-app
- **Service:** `datadog-demo-app`
- **Environment:** `demo`
- **Version:** `1.0.0`

---

## 🚨 Important Notes

This application contains **intentional bugs and vulnerabilities** for demonstration purposes:

- ❌ SQL injection vulnerabilities
- ❌ Memory leaks
- ❌ Runtime exceptions
- ❌ Flaky tests
- ❌ Performance bottlenecks
- ❌ Security misconfigurations

**⚠️ DO NOT use this code in production environments!**

---

## 📚 Additional Resources

- [Source Code Integration Guide](SOURCE_CODE_INTEGRATION.md)
- [Demo Guide](DEMO_GUIDE.md)
- [Traffic Generator Guide](TRAFFIC_GENERATOR_GUIDE.md)
- [Main README](../README.md)

---

**Questions?** Open an issue on [GitHub](https://github.com/eranrh86/datadog-demo-app/issues)

