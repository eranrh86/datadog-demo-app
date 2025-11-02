# 🎯 Datadog Demo Guide

## Pre-Demo Setup (5 minutes)

### 1. Deploy the Application
```bash
cd /Users/eran.rahmani/datadog-demo-app
./scripts/deploy.sh
```

### 2. Generate Initial Data
```bash
./scripts/test-demo.sh
```

### 3. Verify Datadog Integration
- Check that logs are flowing in Datadog
- Verify APM traces are appearing
- Confirm agent is connected

---

## 🎬 Demo Script (15-20 minutes)

### **Feature 1: Log Annotations & Volume Gauging** (3 minutes)

**What to Show:**
- Custom log volume metrics
- Structured logging with business context
- Real-time log volume monitoring

**Demo Steps:**
```bash
# Generate log volume
curl http://$(minikube ip):30080/
curl http://$(minikube ip):30080/api/health/metrics
curl http://$(minikube ip):30080/api/users
```

**In Datadog:**
1. Navigate to Logs → Analytics
2. Show custom metrics: `app.log_volume`, `http.request.count`
3. Demonstrate log search with structured fields
4. Show log volume trending over time

**Key Points:**
- "See how we can gauge log volumes directly from our code"
- "Custom business metrics are automatically tracked"
- "Structured logging makes searching and filtering easy"

---

### **Feature 2: Code Insights - Runtime Errors** (4 minutes)

**What to Show:**
- Runtime error detection
- Vulnerability scanning
- Performance issue identification

**Demo Steps:**
```bash
# Trigger runtime errors
curl http://$(minikube ip):30080/api/users/999
curl http://$(minikube ip):30080/api/orders/666
curl http://$(minikube ip):30080/error/runtime

# Show static analysis
npm run lint
```

**In Datadog:**
1. Navigate to Code Insights
2. Show runtime errors appearing in real-time
3. Demonstrate error grouping and frequency
4. Show vulnerability alerts from static analysis

**Key Points:**
- "Datadog automatically detects runtime errors as they happen"
- "Static analysis catches vulnerabilities before deployment"
- "See the exact line of code causing issues"

---

### **Feature 3: View in IDE Integration** (2 minutes)

**What to Show:**
- Direct navigation from Datadog to source code
- Stack trace integration
- File and line number precision

**Demo Steps:**
```bash
# Generate error with stack trace
curl http://$(minikube ip):30080/error/runtime
```

**In Datadog:**
1. Go to APM → Error Tracking
2. Click on the runtime error
3. Click "View in IDE" button
4. Show how it opens the exact file and line

**Key Points:**
- "Jump directly from error to source code"
- "No more hunting through files to find issues"
- "Exact line number precision"

---

### **Feature 4: Exception Replay** (3 minutes)

**What to Show:**
- Full request/response context
- User session data
- Environment state at time of error

**Demo Steps:**
```bash
# Create detailed error context
curl -X POST http://$(minikube ip):30080/api/orders \
  -H "Content-Type: application/json" \
  -d '{"userId":"invalid","product":"Test","amount":"not-a-number"}'

curl http://$(minikube ip):30080/vulnerable/'; DROP TABLE users; --"
```

**In Datadog:**
1. Navigate to Exception Replay
2. Show full request context
3. Demonstrate user session tracking
4. Show environment variables and system state

**Key Points:**
- "See exactly what the user was doing when the error occurred"
- "Full request/response data for debugging"
- "System state captured at the moment of failure"

---

### **Feature 5: Static Code Analysis** (2 minutes)

**What to Show:**
- Pre-commit vulnerability detection
- Security issue identification
- Code quality metrics

**Demo Steps:**
```bash
# Run security scanning
npm run lint
npm run security-scan
```

**In Datadog:**
1. Show Code Analysis dashboard
2. Demonstrate vulnerability trends
3. Show security score and recommendations

**Key Points:**
- "Catch security issues before they reach production"
- "Automated scanning in your CI/CD pipeline"
- "Track security posture over time"

---

### **Feature 6: Flaky Test Detection** (2 minutes)

**What to Show:**
- Flaky test identification
- Test reliability metrics
- Historical test performance

**Demo Steps:**
```bash
# Run flaky tests multiple times
npm test
npm test
npm test
```

**In Datadog:**
1. Navigate to CI Visibility
2. Show flaky test detection
3. Demonstrate test reliability trends
4. Show impact on deployment confidence

**Key Points:**
- "Automatically identify unreliable tests"
- "Track test performance over time"
- "Improve deployment confidence"

---

## 🔧 Troubleshooting

### If Application Won't Start:
```bash
# Check minikube status
minikube status --profile eran-k8

# Restart if needed
minikube start --profile eran-k8

# Rebuild and redeploy
./scripts/deploy.sh
```

### If No Data in Datadog:
```bash
# Check agent connectivity
kubectl get pods -n datadog

# Verify agent logs
kubectl logs -l app=datadog-agent -n datadog

# Generate more test data
./scripts/test-demo.sh
```

### If Tests Don't Show Flaky Behavior:
```bash
# Run tests multiple times
for i in {1..5}; do npm test; done
```

---

## 📊 Key Metrics to Highlight

### Custom Business Metrics:
- `app.log_volume` - Log volume tracking
- `http.request.count` - Request rate
- `http.request.duration` - Response times
- `orders.created_count` - Business KPIs
- `users.total_count` - User metrics

### Error Tracking:
- Runtime exceptions per minute
- Security vulnerability count
- Performance degradation alerts
- Test failure rates

### Performance Monitoring:
- Memory usage trends
- Response time percentiles
- Database query performance
- Cache hit rates

---

## 🎯 Demo Success Criteria

✅ **Log Annotations**: Show custom metrics in Datadog dashboards  
✅ **Code Insights**: Demonstrate real-time error detection  
✅ **View in IDE**: Successfully navigate from Datadog to source code  
✅ **Static Analysis**: Show vulnerability detection in action  
✅ **Exception Replay**: Display full error context and debugging info  
✅ **Flaky Tests**: Identify unreliable tests and their impact  

---

## 📞 Quick Commands Reference

```bash
# Deploy application
./scripts/deploy.sh

# Generate demo data
./scripts/test-demo.sh

# Run flaky tests
npm test

# Check security issues
npm run lint

# View application logs
kubectl logs -f deployment/datadog-demo-app -n datadog-demo

# Get application URL
echo "http://$(minikube ip):30080"
```
