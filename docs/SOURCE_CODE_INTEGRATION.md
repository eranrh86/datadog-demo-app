# 🔗 Datadog Source Code Integration Setup

This document explains how to set up Datadog's source code integration for the datadog-demo-app, enabling features like "View in IDE" and code snippets in APM traces.

## 📋 Overview

The source code integration links your telemetry (traces, errors, profiles) to your Git repository, allowing you to:
- Jump directly from Datadog to specific lines of code in your IDE
- View code snippets in APM traces and error tracking
- Debug issues faster with instant code context

## ✅ What's Already Configured

This repository is **pre-configured** with all necessary settings:

### 1. Dockerfile Configuration
The `Dockerfile` includes Git metadata build arguments:
```dockerfile
ARG DD_GIT_REPOSITORY_URL
ARG DD_GIT_COMMIT_SHA
ENV DD_GIT_REPOSITORY_URL=${DD_GIT_REPOSITORY_URL}
ENV DD_GIT_COMMIT_SHA=${DD_GIT_COMMIT_SHA}
```

### 2. Application Configuration
The `src/app.js` sets Git metadata environment variables:
```javascript
process.env.DD_GIT_REPOSITORY_URL = process.env.DD_GIT_REPOSITORY_URL || 'https://github.com/eranrh86/datadog-demo-app';
process.env.DD_GIT_COMMIT_SHA = process.env.DD_GIT_COMMIT_SHA || '';
```

### 3. Kubernetes Configuration
The `k8s/deployment.yaml` includes Git environment variables:
```yaml
- name: DD_GIT_REPOSITORY_URL
  value: "https://github.com/eranrh86/datadog-demo-app"
- name: DD_GIT_COMMIT_SHA
  value: "REPLACE_WITH_COMMIT_SHA"
```

## 🚀 Usage

### Option 1: Docker Build with Git Metadata

Use the provided build script:

```bash
./build-with-git-metadata.sh
```

This script automatically:
- Retrieves your current Git repository URL
- Gets the current commit SHA
- Builds the Docker image with proper build args

Or build manually:

```bash
docker build . \
  -t datadog-demo-app:latest \
  --build-arg DD_GIT_REPOSITORY_URL=$(git config --get remote.origin.url) \
  --build-arg DD_GIT_COMMIT_SHA=$(git rev-parse HEAD)
```

### Option 2: Kubernetes Deployment

1. **Get your current commit SHA:**
   ```bash
   git rev-parse HEAD
   ```

2. **Update `k8s/deployment.yaml`:**
   Replace `REPLACE_WITH_COMMIT_SHA` with your actual commit SHA:
   ```yaml
   - name: DD_GIT_COMMIT_SHA
     value: "abc123def456..."  # Your commit SHA
   ```

3. **Build the image with Git metadata:**
   ```bash
   ./build-with-git-metadata.sh
   ```

4. **Deploy to Kubernetes:**
   ```bash
   kubectl apply -f k8s/
   ```

### Option 3: Local Development

For local development, set environment variables:

```bash
export DD_GIT_REPOSITORY_URL="https://github.com/eranrh86/datadog-demo-app"
export DD_GIT_COMMIT_SHA=$(git rev-parse HEAD)
npm start
```

## 🔍 Verification

### 1. Check Environment Variables

Once your application is running, verify the Git metadata is set:

```bash
# For Docker
docker exec <container-id> env | grep DD_GIT

# For Kubernetes
kubectl exec -it <pod-name> -n datadog-demo -- env | grep DD_GIT
```

You should see:
```
DD_GIT_REPOSITORY_URL=https://github.com/eranrh86/datadog-demo-app
DD_GIT_COMMIT_SHA=abc123def456...
```

### 2. Verify in Datadog

1. **Go to Datadog:** https://app.datadoghq.com
2. **Navigate to:** APM → Services → `datadog-demo-app`
3. **Click on any trace**
4. **Look for:** "View in IDE" or "View Code" buttons
5. **Click the button** - it should open the exact file and line in your IDE!

## 🎯 Testing the Integration

Generate some errors to test the integration:

```bash
# Trigger a runtime error
curl http://localhost:3000/error/runtime

# Trigger a user not found error
curl http://localhost:3000/api/users/999

# Trigger an order error
curl http://localhost:3000/api/orders/666
```

Then in Datadog:
1. Go to **APM → Error Tracking**
2. Click on any error
3. Click **"View in IDE"**
4. Your IDE should open to the exact line that caused the error!

## 🔧 Troubleshooting

### Code Links Not Working

If "View in IDE" doesn't appear or doesn't work:

1. **Verify Git metadata is set:**
   ```bash
   docker exec <container> env | grep DD_GIT
   ```

2. **Check commit SHA matches deployed code:**
   - The commit SHA should match the code that's actually running
   - If you've made changes since building, rebuild with current SHA

3. **Verify repository URL is correct:**
   ```bash
   git config --get remote.origin.url
   # Should be: https://github.com/eranrh86/datadog-demo-app.git
   ```

4. **Check Datadog tracer version:**
   - Requires `dd-trace` version 3.21.0 or higher
   - Check `package.json` for version

### Source Maps Not Working (TypeScript)

For TypeScript or transpiled apps:
1. Generate source maps during build
2. Publish source maps with the application
3. Run Node.js with `--enable-source-maps` flag (already configured in Dockerfile)

## 📚 Additional Resources

- [Datadog Source Code Integration Docs](https://docs.datadoghq.com/integrations/guide/source-code-integration/)
- [Node.js APM Setup](https://docs.datadoghq.com/tracing/setup_overview/setup/nodejs/)
- [Error Tracking](https://docs.datadoghq.com/tracing/error_tracking/)

## 🎉 What's Next?

Once configured, you can:
- **Debug production issues faster** - Jump from errors to code instantly
- **Understand performance bottlenecks** - See exact code causing slow traces
- **Review code changes** - Link deploys to commits
- **Collaborate better** - Share direct links to problematic code

---

**Questions?** Check the [main README](../README.md) or open an issue on GitHub.

