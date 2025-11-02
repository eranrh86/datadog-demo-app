# 🎯 Datadog Demo Cheat Sheet - Quick Reference

## 🚀 **Setup Commands**
```bash
cd /Users/eran.rahmani/datadog-demo-app
./start-demo.sh
```

## 📁 **Key Files to Open in Cursor**

| File | Purpose | Key Lines |
|------|---------|-----------|
| `src/utils/logger.js` | Log annotations | 64-90 |
| `src/app.js` | Vulnerabilities | 73-78, 95-99 |
| `src/middleware/errorHandler.js` | Exception replay | 5-20 |
| `tests/users.test.js` | Flaky tests | 50-60 |
| `logs/combined.log` | Live logs | Latest entries |

## 🎬 **Demo Commands**

### **Generate Log Annotations**
```bash
curl http://localhost:3000/api/users
curl http://localhost:3000/api/orders
curl http://localhost:3000/api/health
```

### **Trigger Errors**
```bash
curl http://localhost:3000/api/users/999        # Runtime error
curl http://localhost:3000/vulnerable/123       # Security vulnerability
curl http://localhost:3000/error/runtime        # Exception replay
```

### **Show Static Analysis**
```bash
npm run lint                                    # Security issues
```

### **Run Flaky Tests**
```bash
npm test                                        # Run multiple times
```

### **View Live Logs**
```bash
tail -f logs/combined.log | jq .               # Pretty JSON logs
```

## 🎯 **Cursor Shortcuts**

| Shortcut | Action |
|----------|--------|
| `Cmd+Shift+P` | Command Palette |
| `Cmd+P` | Quick file open |
| `Cmd+G` | Go to line |
| `Cmd+J` | Toggle terminal |
| `Cmd+Shift+M` | Problems panel |

## 📊 **What to Highlight**

### **Log Annotations**
- `dd_custom_metric: true`
- `trace_id` correlation
- Business context

### **Code Insights**
- ESLint security warnings
- Runtime error detection
- Performance issues

### **Exception Replay**
- Full request context
- Stack traces
- Environment data

### **Flaky Tests**
- Random failures
- Timing issues
- CI reliability

## 🎪 **Demo Flow (15 minutes)**

1. **[2 min]** Show code structure in Cursor
2. **[3 min]** Log annotations - code + live output
3. **[3 min]** Code insights - static analysis
4. **[2 min]** View in IDE - error navigation
5. **[3 min]** Exception replay - rich context
6. **[2 min]** Flaky tests - reliability issues

## 🔧 **Troubleshooting**

### **If app not responding:**
```bash
lsof -ti:3000 | xargs kill -9
./start-demo.sh
```

### **If no logs appearing:**
```bash
ls -la logs/
tail logs/combined.log
```

### **If Datadog extension not working:**
- Check sidebar for Datadog icon
- Restart Cursor: `Cmd+Shift+P` → "Developer: Reload Window"

---

**🎯 You're ready for an amazing demo! 🚀**
