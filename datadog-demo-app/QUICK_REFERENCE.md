# 🚀 Quick Reference Card

**Repository:** https://github.com/eranrh86/datadog-demo-app  
**Service:** `datadog-demo-app`

---

## ⚡ Quick Start

```bash
# 1. Verify all features
./verify-datadog-features.sh

# 2. Build with Git metadata
./build-with-git-metadata.sh

# 3. Run demo
./demo-all-features.sh
```

---

## 🎯 5 Key Features

### 1️⃣ Code Insights
**What:** Runtime errors & vulnerabilities detection  
**Test:** `curl http://localhost:3000/api/users/999`  
**View:** Datadog → APM → Error Tracking

### 2️⃣ View in IDE
**What:** Jump from Datadog to source code  
**Test:** Trigger error → Click "View in IDE" in Datadog  
**View:** Error Tracking → Click error → "View in IDE" button

### 3️⃣ Static Code Analysis
**What:** Pre-commit security checks  
**Test:** `npm run lint`  
**View:** Datadog → Code Insights → Vulnerabilities

### 4️⃣ Exception Replay
**What:** Full error context for debugging  
**Test:** `curl http://localhost:3000/api/orders/666`  
**View:** Error Tracking → Click error → See full context

### 5️⃣ Fix in Chat (Cursor Only)
**What:** AI-powered code fixes in IDE  
**Test:** In Cursor, Cmd+K → "Fix this error"  
**View:** Cursor → AI suggests fix with explanation

---

## 🔥 Demo Endpoints

| Endpoint | Feature | What It Shows |
|----------|---------|---------------|
| `GET /api/users/999` | Code Insights | Null pointer exception |
| `GET /api/orders/666` | Exception Replay | Intentional error with context |
| `GET /error/runtime` | View in IDE | Runtime error with source mapping |
| `GET /vulnerable/123` | Code Insights | SQL injection vulnerability |
| `GET /api/health/ready` | Exception Replay | Health check failures |
| `npm run lint` | Static Analysis | Security issues detection |
| `npm test` | Flaky Tests | Random test failures |

---

## 📊 Datadog Navigation

```
APM
├── Services → datadog-demo-app
├── Error Tracking → See all errors
│   └── Click error → "View in IDE"
└── Traces → See all requests

Code Insights
├── Runtime Errors → See exceptions
└── Vulnerabilities → See security issues

CI/CD
└── Test Visibility → Flaky Tests
```

---

## 🛠️ Build & Deploy

```bash
# Build with Git metadata
./build-with-git-metadata.sh

# Docker
docker run -d -p 3000:3000 \
  -e DD_API_KEY=$DD_API_KEY \
  datadog-demo-app:latest

# Kubernetes
kubectl apply -f k8s/
```

---

## 🧪 Test Commands

```bash
# Runtime errors
curl http://localhost:3000/api/users/999
curl http://localhost:3000/api/orders/666
curl http://localhost:3000/error/runtime

# Security vulnerabilities
curl http://localhost:3000/vulnerable/123
curl "http://localhost:3000/vulnerable/'; DROP TABLE users; --"

# Health check errors
curl http://localhost:3000/api/health/ready

# Static analysis
npm run lint

# Flaky tests
npm test
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/app.js` | Main app with Datadog init & Git metadata |
| `src/routes/users.js` | User routes with runtime errors |
| `src/routes/orders.js` | Order routes with errors |
| `src/routes/health.js` | Health checks with failures |
| `Dockerfile` | Docker build with Git metadata |
| `k8s/deployment.yaml` | K8s deployment with Git metadata |
| `.eslintrc.js` | ESLint security configuration |
| `build-with-git-metadata.sh` | Build script |
| `verify-datadog-features.sh` | Verification script |
| `demo-all-features.sh` | Complete demo script |

---

## 🔍 Verification Checklist

- [ ] Git metadata configured (`DD_GIT_REPOSITORY_URL`, `DD_GIT_COMMIT_SHA`)
- [ ] Datadog tracer initialized (`dd-trace@4.20.0+`)
- [ ] Error tracking enabled
- [ ] Log injection enabled (`logInjection: true`)
- [ ] ESLint with security plugin configured
- [ ] Runtime errors working (test with `/api/users/999`)
- [ ] "View in IDE" button appears in Datadog
- [ ] Static analysis detects vulnerabilities
- [ ] Exception Replay shows full context

---

## 🎬 Demo Script

1. **Show Static Analysis**
   ```bash
   npm run lint
   ```
   → Show security issues in terminal

2. **Trigger Runtime Errors**
   ```bash
   curl http://localhost:3000/api/users/999
   ```
   → Show in Datadog Error Tracking

3. **Demonstrate View in IDE**
   - Click error in Datadog
   - Click "View in IDE"
   - Show it opens exact file/line in IDE

4. **Show Exception Replay**
   ```bash
   curl http://localhost:3000/api/orders/666
   ```
   → Show full request/response context in Datadog

5. **Show Flaky Tests**
   ```bash
   npm test
   npm test
   npm test
   ```
   → Show in CI/CD Test Visibility

---

## 🔗 Links

- **Datadog:** https://app.datadoghq.com
- **GitHub:** https://github.com/eranrh86/datadog-demo-app
- **Docs:** [docs/FEATURES_CHECKLIST.md](docs/FEATURES_CHECKLIST.md)

---

## ⚠️ Remember

This app has **intentional bugs** for demo purposes!  
**DO NOT use in production!**

---

**Need help?** Run `./verify-datadog-features.sh`

