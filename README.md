# 🐕 Datadog Demo Application

<div align="center">

![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)
![Express](https://img.shields.io/badge/express-4.x-blue.svg)
![Datadog](https://img.shields.io/badge/datadog-integrated-purple.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A comprehensive Node.js application showcasing **Datadog's full observability stack** - perfect for demos and learning.

[Features](#-features) • [Quick Start](#-quick-start) • [Demo Scenarios](#-demo-scenarios) • [Documentation](#-documentation)

</div>

---

## ✨ Features

This demo application demonstrates all key Datadog developer features:

### 📊 **Observability & Monitoring**
- **APM Tracing** - Distributed tracing across all endpoints
- **Log Management** - Structured JSON logs with trace correlation
- **Custom Metrics** - Business and system metrics with `logger.gauge()`
- **Real User Monitoring** - Performance tracking and analytics

### 🔍 **Developer Experience**
- **Code Insights** - Runtime error detection and security vulnerability scanning
- **Exception Replay** - Detailed error context with request/response data
- **View in IDE** - Jump from Datadog directly to source code
- **Static Analysis** - Pre-commit vulnerability detection with ESLint + Snyk

### 🧪 **Testing & Quality**
- **Flaky Test Detection** - Identify unreliable tests automatically
- **Performance Profiling** - Memory and CPU profiling
- **Security Scanning** - SQL injection and vulnerability detection

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 16+ and npm
- **Docker** (optional, for containerized deployment)
- **Kubernetes/Minikube** (optional, for K8s deployment)
- **Datadog Account** with API and APP keys

### Installation

```bash
# Clone the repository
git clone https://github.com/eranrh86/datadog-demo-app.git
cd datadog-demo-app

# Install dependencies
npm install

# Set up environment variables
export DD_API_KEY=your_api_key_here
export DD_SERVICE=datadog-demo-app
export DD_ENV=demo
export DD_VERSION=1.0.0

# Start the application
npm start
```

The application will be available at `http://localhost:3000`

### Docker Deployment

```bash
# Build the Docker image
docker build -t datadog-demo-app .

# Run with Datadog agent
docker run -d \
  -p 3000:3000 \
  -e DD_API_KEY=your_api_key \
  -e DD_SERVICE=datadog-demo-app \
  -e DD_ENV=demo \
  datadog-demo-app
```

### Kubernetes Deployment

```bash
# Deploy to your cluster
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml

# Or use the deployment script
./scripts/deploy.sh
```

---

## 🎬 Demo Scenarios

### 1️⃣ Log Annotations & Custom Metrics

```bash
# Generate logs with custom metrics
curl http://localhost:3000/
curl http://localhost:3000/api/health

# View in Datadog: Logs → Custom Metrics Dashboard
```

**What to show:**
- Real-time log volume gauging
- Custom business metrics
- Structured logging with trace correlation

### 2️⃣ Exception Replay & Error Tracking

```bash
# Trigger intentional errors
curl http://localhost:3000/api/users/999
curl http://localhost:3000/api/orders/666
curl http://localhost:3000/error/runtime

# View in Datadog: APM → Error Tracking → Exception Replay
```

**What to show:**
- Full request/response context
- Stack traces with source code
- User session information
- Environment state at error time

### 3️⃣ Code Insights & Security

```bash
# Run static analysis
npm run lint

# Trigger security vulnerabilities
curl "http://localhost:3000/vulnerable/'; DROP TABLE users; --"

# View in Datadog: Code Insights → Vulnerabilities
```

**What to show:**
- SQL injection detection
- Security vulnerability alerts
- Code quality issues
- Performance bottlenecks

### 4️⃣ View in IDE Integration

```bash
# Generate error with stack trace
curl http://localhost:3000/error/runtime

# In Datadog: Click "View in IDE" from error trace
```

**What to show:**
- Direct jump from Datadog to source code
- Exact file and line number navigation
- Seamless developer workflow

### 5️⃣ Flaky Test Detection

```bash
# Run tests multiple times
npm test
npm test
npm test

# View in Datadog: CI/CD → Test Visibility → Flaky Tests
```

**What to show:**
- Flaky test identification
- Test reliability metrics
- Failure patterns and trends

### 6️⃣ APM & Performance Monitoring

```bash
# Generate traffic
./traffic-generator.sh

# Or use the test script
./scripts/test-demo.sh

# View in Datadog: APM → Services → datadog-demo-app
```

**What to show:**
- Distributed tracing
- Service dependencies
- Performance metrics
- Database query monitoring

---

## 📚 API Endpoints

### Normal Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Homepage with log annotations |
| `/api/health` | GET | Health check with metrics |
| `/api/users` | GET | List all users |
| `/api/users/:id` | GET | Get user by ID |
| `/api/orders` | GET | List all orders |
| `/api/orders/:id` | GET | Get order by ID |

### Error Scenarios (Demo)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/999` | GET | Null pointer exception |
| `/api/orders/666` | GET | Intentional error |
| `/api/orders/500` | GET | Database error simulation |
| `/error/runtime` | GET | Runtime error |

### Security Vulnerabilities (Demo)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/vulnerable/:id` | GET | SQL injection vulnerability |
| `/memory-leak` | GET | Memory leak simulation |

---

## 🏗️ Project Structure

```
datadog-demo-app/
├── src/
│   ├── app.js                 # Main application with Datadog integration
│   ├── middleware/
│   │   ├── errorHandler.js    # Global error handling
│   │   └── requestLogger.js   # Request/response logging
│   ├── routes/
│   │   ├── health.js          # Health check endpoints
│   │   ├── orders.js          # Order management (with errors)
│   │   └── users.js           # User management (with errors)
│   └── utils/
│       └── logger.js          # Custom logger with Datadog metrics
├── tests/
│   ├── users.test.js          # User API tests (some flaky)
│   ├── orders.test.js         # Order API tests (some flaky)
│   └── setup.js               # Test configuration
├── k8s/
│   ├── namespace.yaml         # Kubernetes namespace
│   ├── configmap.yaml         # Configuration
│   └── deployment.yaml        # Deployment with Datadog labels
├── scripts/
│   ├── deploy.sh              # Deployment automation
│   ├── test-demo.sh           # Demo scenario runner
│   └── quick-demo.sh          # Quick demo setup
├── docs/                      # Additional documentation
├── Dockerfile                 # Container configuration
├── package.json               # Dependencies and scripts
└── README.md                  # This file
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Datadog Configuration
DD_SERVICE=datadog-demo-app        # Service name
DD_ENV=demo                         # Environment
DD_VERSION=1.0.0                    # Version
DD_API_KEY=<your-api-key>          # Datadog API key
DD_LOGS_INJECTION=true             # Enable log correlation
DD_RUNTIME_METRICS_ENABLED=true    # Runtime metrics
DD_PROFILING_ENABLED=true          # Continuous profiling
DD_TRACE_SAMPLE_RATE=1             # 100% trace sampling
DD_TRACE_ANALYTICS_ENABLED=true    # Enable analytics

# Application Configuration
NODE_ENV=production                # Environment mode
LOG_LEVEL=info                     # Logging level
PORT=3000                          # Application port
```

### Kubernetes Labels

```yaml
labels:
  tags.datadoghq.com/service: "datadog-demo-app"
  tags.datadoghq.com/env: "demo"
  tags.datadoghq.com/version: "1.0.0"
```

---

## 📖 Documentation

- **[Demo Guide](docs/DEMO_GUIDE.md)** - Complete demo walkthrough
- **[Cursor Integration](docs/CURSOR_DEMO_GUIDE.md)** - IDE integration setup
- **[Traffic Generator](docs/TRAFFIC_GENERATOR_GUIDE.md)** - Load testing guide
- **[Source Code Integration](docs/SOURCE_CODE_INTEGRATION.md)** - View in IDE setup

---

## 🚨 Important Notes

> ⚠️ **This application contains intentional bugs and vulnerabilities for demonstration purposes:**
> - SQL injection vulnerabilities
> - Memory leaks
> - Runtime exceptions
> - Flaky tests
> - Performance bottlenecks
> - Security misconfigurations
>
> **DO NOT use this code in production environments!**

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

For questions or issues:
- **Email**: your-se@datadoghq.com
- **GitHub Issues**: [Create an issue](https://github.com/eranrh86/datadog-demo-app/issues)
- **Datadog Docs**: [docs.datadoghq.com](https://docs.datadoghq.com)

---

<div align="center">

**Made with ❤️ for Datadog Demos**

⭐ Star this repo if you find it helpful!

</div>
