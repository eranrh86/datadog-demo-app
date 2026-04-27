#!/bin/bash

# Continuous Error Generator
# Generates one error per minute

LOGFILE="/tmp/error-generator.log"
PIDFILE="/tmp/error-generator.pid"

echo "🔥 Starting Continuous Error Generator" | tee -a "$LOGFILE"
echo "📊 Generating errors every 60 seconds..." | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

# Save PID
echo $$ > "$PIDFILE"

# Counter
COUNT=0

while true; do
  COUNT=$((COUNT + 1))
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  
  # Get pod name
  POD_NAME=$(kubectl get pods -n datadog-demo -l app=datadog-demo-app -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  
  if [ -z "$POD_NAME" ]; then
    echo "[$TIMESTAMP] ⚠️  Error #$COUNT - No pod found" | tee -a "$LOGFILE"
  else
    # Generate error
    kubectl exec -n datadog-demo "$POD_NAME" -- wget -q -O- http://localhost:3000/api/users/999 > /dev/null 2>&1
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 1 ] || [ $EXIT_CODE -eq 8 ]; then
      echo "[$TIMESTAMP] ✅ Error #$COUNT generated successfully (HTTP 500)" | tee -a "$LOGFILE"
    else
      echo "[$TIMESTAMP] ⚠️  Error #$COUNT - Unexpected exit code: $EXIT_CODE" | tee -a "$LOGFILE"
    fi
  fi
  
  # Wait 60 seconds
  sleep 60
done

