# 📄 Datadog Demo - Printable Cheat Sheet

**Print this and keep it next to you during the demo!**

---

## ⚡ Quick Setup (Run these first)

```bash
cd /Users/eran.rahmani/datadog-demo-app
./build-with-git-metadata.sh

export DD_API_KEY=your_key_here

docker run -d --name datadog-demo-app -p 3000:3000 \
  -e DD_API_KEY=$DD_API_KEY \
  -e DD_AGENT_HOST=host.docker.internal \
  datadog-demo-app:latest

# Wait 30 seconds, then verify
curl http://localhost:3000/api/health
```

---

## 🎬 Demo Flow (Copy/Paste These)

### 1. Static Code Analysis (3 min)

```bash
npm run lint
```

**Say:** "Detects security issues pre-commit - SQL injection, eval, object injection"

**Show:** src/app.js lines 84-87

---

### 2. Code Insights - Runtime Errors (5 min)

```bash
curl http://localhost:3000/api/users/999
curl http://localhost:3000/api/orders/666
curl http://localhost:3000/error/runtime
```

**Say:** "Automatic error detection with full stack traces"

**Show:** Datadog → APM → Error Tracking

---

### 3. View in IDE (5 min)

```bash
curl http://localhost:3000/api/users/999
```

**Say:** "Jump from Datadog to exact line of code in GitHub"

**Show:** 
1. Datadog → Error Tracking → Click error
2. Click "View in IDE" button
3. Opens: github.com/eranrh86/datadog-demo-app/blob/c164a76/src/routes/users.js#L48

---

### 4. Exception Replay (5 min)

```bash
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"userId":"invalid","product":"Test","amount":"not-a-number"}'

curl http://localhost:3000/api/orders/666
```

**Say:** "Full request/response context, environment state, correlated logs"

**Show:** Datadog → Error → Overview/Infrastructure/Logs tabs

---

### 5. Flaky Tests (3 min)

```bash
npm test
npm test
npm test
```

**Say:** "Automatic detection of unreliable tests"

**Show:** Datadog → CI/CD → Test Visibility

---

## 🎯 Key Talking Points

### Code Insights
✅ No code changes required  
✅ Automatic error detection  
✅ Security vulnerability scanning  

### View in IDE
✅ One-click jump to source  
✅ Always shows deployed version  
✅ Works with any Git provider  

### Static Analysis
✅ Pre-commit detection  
✅ IDE integration  
✅ Security-focused rules  

### Exception Replay
✅ Full error context  
✅ Easy reproduction  
✅ Privacy controls available  

---

## 📊 Datadog Navigation

```
APM → Services → datadog-demo-app
APM → Error Tracking → Click error → "View in IDE"
Code Insights → Vulnerabilities
CI/CD → Test Visibility → Flaky Tests
```

---

## 🔗 Key URLs

**GitHub:** https://github.com/eranrh86/datadog-demo-app  
**Service:** datadog-demo-app  
**Commit:** c164a76

---

## ⚠️ Remember

- Wait 30s after deploy for data to flow
- Show code FIRST, then Datadog UI
- Emphasize "no code changes required"
- Highlight "View in IDE" button
- Show full context in Exception Replay

---

## 🧹 Cleanup

```bash
docker stop datadog-demo-app && docker rm datadog-demo-app
```

---

## 🆘 Troubleshooting

**No data in Datadog?**
- Wait 30 more seconds
- Check DD_API_KEY is set
- Verify app is running: `docker ps`

**"View in IDE" not showing?**
- Check Git metadata: `docker exec datadog-demo-app env | grep DD_GIT`
- Should see DD_GIT_REPOSITORY_URL and DD_GIT_COMMIT_SHA

**Errors not appearing?**
- Trigger again: `curl http://localhost:3000/api/users/999`
- Check Error Tracking filter: Service = datadog-demo-app

---

## 📞 Q&A Prep

**Q: Does this work with our code?**  
A: Yes! Just add Datadog tracer + Git metadata

**Q: What about sensitive data?**  
A: Extensive privacy controls available

**Q: Performance overhead?**  
A: Less than 1% typically

**Q: What languages?**  
A: Java, Python, Ruby, Go, Node.js, .NET, PHP, more

---

## ✅ Pre-Demo Checklist

- [ ] App built and deployed
- [ ] Datadog UI open
- [ ] Terminal ready
- [ ] IDE open to src/app.js
- [ ] Data flowing (wait 30s)
- [ ] Test one endpoint works

---

**Good luck! 🚀**

