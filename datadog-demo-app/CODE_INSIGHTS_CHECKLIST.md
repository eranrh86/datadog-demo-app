# 🎯 CODE INSIGHTS - VERIFICATION CHECKLIST

## ✅ Configuration Complete!

### What's Configured:
- ✅ Code Insights: **enabled**
- ✅ Error Tracking: **enabled**
- ✅ Service Filter: **datadog-demo-app** (not eran-njs!)
- ✅ Path Mapping: **/app → /Users/eran.rahmani/datadog-demo-app**
- ✅ Logs: **still working**
- ✅ Error Generator: **running** (1/min)

---

## 🎯 What You Should See After Reload:

### 1. Red Squiggle on Line 48
**File:** `src/routes/users.js`

```javascript
48| return res.json({ user: undefinedUser.profile.details });
                             ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                             🔴 Red squiggle here!
```

### 2. Hover Details
When you hover over the red squiggle:
```
TypeError: Cannot read properties of null
├─ 5 occurrences in the last hour
├─ Last seen: 2 minutes ago
└─ View in Datadog Error Tracking →
```

### 3. Code Insights View
**Open with:** `Cmd + Shift + P → "Datadog: Focus on Code Insights View"`

Should show:
```
CODE INSIGHTS (1)
├─ Error Tracking (1)
│  └─ TypeError: Cannot read properties of null (reading 'profile')
│     📁 src/routes/users.js:48
│     🔍 Click to jump to error
```

---

## 🚀 RELOAD NOW!

```
Cmd + Shift + P → "Developer: Reload Window"
```

Then wait 3 minutes and check `src/routes/users.js` line 48!

---

## 🔍 If No Squiggle After 5 Minutes:

1. **Check Extension Logs:**
   ```
   Cmd + Shift + U → Select "Datadog" from dropdown
   ```
   Look for:
   - "Fetching Code Insights..."
   - "Found X errors"
   - Any error messages

2. **Check Code Insights View:**
   - Does it list the error?
   - Is service filter showing "datadog-demo-app"?

3. **Share with me:**
   - Screenshot of line 48
   - Extension logs
   - Code Insights view

