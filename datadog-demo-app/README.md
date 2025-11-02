# Datadog Demo Application

A comprehensive Node.js application designed to demonstrate all key Datadog developer features for your demo presentation.

## 🎯 Demo Features Covered

### 1. **Log Annotations & Volume Gauging**
- Custom log volume metrics with `logger.gauge()`
- Request/response logging with structured data
- Performance metrics and histograms
- Business logic annotations

### 2. **Code Insights**
- **Runtime Errors**: Intentional exceptions for Exception Replay
- **Security Vulnerabilities**: SQL injection, eval usage, input validation issues
- **Performance Issues**: Memory leaks, slow queries, cache misses
- **Flaky Tests**: Timing-dependent and race condition tests

### 3. **View in IDE Integration**
- Proper source mapping and file references
- Structured logging with file/line information
- Error stack traces pointing to source code

### 4. **Static Code Analysis**
- ESLint with security plugin configuration
- Snyk vulnerability scanning
- Code quality rules and best practices

### 5. **Exception Replay**
- Detailed error context and stack traces
- Request/response data capture
- User session information
- Environment and system state

### 6. **APM Tracing**
- Distributed tracing across all endpoints
- Database query monitoring simulation
- External API call tracing
- Custom span annotations

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- Docker
- Minikube with `eran-k8` profile
- Datadog Agent configured in your cluster

### 1. Deploy to Minikube
```bash
# Clone and navigate to the project
cd /Users/eran.rahmani/datadog-demo-app

# Install dependencies
npm install

# Deploy to minikube
./scripts/deploy.sh
```

### 2. Generate Demo Data
```bash
# Run test scenarios to generate logs, traces, and errors
./scripts/test-demo.sh
```

### 3. Run Flaky Tests
```bash
# Demonstrate flaky test detection
npm test
npm run test:flaky
```

### 4. Static Code Analysis
```bash
# Run linting (will show security issues)
npm run lint

# Run security scan
npm run security-scan
```

## 📊 Demo Endpoints

### Normal Operations
- `GET /` - Homepage with log annotations
- `GET /api/health` - Health checks with metrics
- `GET /api/users` - User management with tracing
- `GET /api/orders` - Order processing with performance monitoring

### Error Scenarios (for Exception Replay)
- `GET /api/users/999` - Runtime error (null pointer)
- `GET /api/orders/666` - Intentional exception
- `GET /api/orders/500` - Database connection error
- `GET /error/runtime` - Direct runtime error

### Security Vulnerabilities (for Code Insights)
- `GET /vulnerable/123` - SQL injection vulnerability
- `GET /vulnerable/'; DROP TABLE users; --` - SQL injection attempt

### Performance Issues
- `GET /memory-leak` - Memory leak simulation
- Multiple rapid requests to `/api/orders` - Load testing

## 🎬 Demo Script

### 1. Log Annotations Demo
```bash
# Show log volume gauging
curl http://<minikube-ip>:30080/
curl http://<minikube-ip>:30080/api/health/metrics

# In Datadog: Show custom metrics dashboard
```

### 2. Code Insights Demo
```bash
# Trigger runtime errors
curl http://<minikube-ip>:30080/api/users/999
curl http://<minikube-ip>:30080/api/orders/666

# Run static analysis
npm run lint
npm run security-scan

# In Datadog: Show Code Insights alerts and vulnerabilities
```

### 3. View in IDE Demo
```bash
# Generate error with stack trace
curl http://<minikube-ip>:30080/error/runtime

# In Datadog: Click "View in IDE" from error trace
# Should open the exact file and line in your IDE
```

### 4. Exception Replay Demo
```bash
# Create detailed error context
curl -X POST http://<minikube-ip>:30080/api/orders \
  -H "Content-Type: application/json" \
  -d '{"userId":"invalid","product":"Test","amount":"not-a-number"}'

# In Datadog: Show full request/response context in Exception Replay
```

### 5. Flaky Tests Demo
```bash
# Run tests multiple times to show flaky behavior
npm test
npm test
npm test

# In Datadog: Show flaky test detection and patterns
```

## 🔧 Configuration

### Environment Variables
```bash
# Datadog Configuration
DD_SERVICE=datadog-demo-app
DD_ENV=demo
DD_VERSION=1.0.0
DD_LOGS_INJECTION=true
DD_RUNTIME_METRICS_ENABLED=true
DD_PROFILING_ENABLED=true
DD_TRACE_SAMPLE_RATE=1
DD_TRACE_ANALYTICS_ENABLED=true

# Application Configuration
NODE_ENV=production
LOG_LEVEL=info
PORT=3000
```

### Kubernetes Labels
The application uses proper Datadog labels for service mapping:
```yaml
labels:
  tags.datadoghq.com/service: datadog-demo-app
  tags.datadoghq.com/env: demo
  tags.datadoghq.com/version: "1.0.0"
```

## 📁 Project Structure

```
datadog-demo-app/
├── src/
│   ├── app.js              # Main application with Datadog integration
│   ├── utils/logger.js     # Custom logger with metrics
│   ├── middleware/         # Request logging and error handling
│   └── routes/             # API endpoints with demo scenarios
├── tests/                  # Flaky tests for demonstration
├── k8s/                    # Kubernetes manifests
├── scripts/                # Deployment and testing scripts
├── .eslintrc.js           # Static analysis configuration
├── jest.config.js         # Test configuration
└── Dockerfile             # Container configuration
```

## 🎯 Key Demo Points

1. **Log Volume Metrics**: Show real-time log volume gauging in Datadog dashboards
2. **Security Alerts**: Demonstrate Code Insights detecting vulnerabilities in real-time
3. **Performance Monitoring**: Show slow query detection and memory leak alerts
4. **Error Tracking**: Use Exception Replay to debug production issues
5. **Flaky Test Detection**: Show how Datadog identifies unreliable tests
6. **IDE Integration**: Jump from Datadog directly to source code
7. **Static Analysis**: Show pre-commit vulnerability detection

## 🔍 Monitoring & Observability

The application generates comprehensive telemetry data:
- **Logs**: Structured JSON logs with trace correlation
- **Metrics**: Custom business and system metrics
- **Traces**: Distributed tracing across all operations
- **Errors**: Detailed exception context and stack traces
- **Performance**: Response times, memory usage, and throughput

## 🚨 Intentional Issues (for Demo)

This application contains intentional issues to demonstrate Datadog features:
- SQL injection vulnerabilities
- Memory leaks
- Runtime exceptions
- Flaky tests
- Performance bottlenecks
- Security misconfigurations

**⚠️ Do not use this code in production environments!**

## 📞 Support

For demo questions or issues:
1. Check the application logs: `kubectl logs -f deployment/datadog-demo-app -n datadog-demo`
2. Verify Datadog agent connectivity
3. Ensure all environment variables are set correctly
4. Run the test script to generate sample data
