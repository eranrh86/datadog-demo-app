#!/bin/bash

# 🚀 Background Traffic Generator Manager
# Start, stop, and check status of the continuous log generator

PID_FILE=".traffic-generator.pid"
SCRIPT_NAME="generate-logs-continuously.sh"

case "$1" in
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "❌ Traffic generator is already running (PID: $PID)"
                exit 1
            fi
        fi
        
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║     🚀 Starting Background Traffic Generator              ║"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo ""
        
        # Start in background
        nohup ./$SCRIPT_NAME > logs/traffic-generator.log 2>&1 &
        PID=$!
        echo $PID > "$PID_FILE"
        
        sleep 2
        
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ Traffic generator started successfully"
            echo "   PID: $PID"
            echo "   Log: logs/traffic-generator.log"
            echo ""
            echo "📊 Stats:"
            echo "   - Generates traffic every 60 seconds"
            echo "   - 8+ logs & traces per cycle"
            echo "   - ~480 logs per hour"
            echo ""
            echo "To stop: ./traffic-generator.sh stop"
            echo "To check: ./traffic-generator.sh status"
        else
            echo "❌ Failed to start traffic generator"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
        
    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "❌ Traffic generator is not running"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        
        echo "🛑 Stopping traffic generator (PID: $PID)..."
        
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            sleep 1
            
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
            fi
            
            echo "✅ Traffic generator stopped"
        else
            echo "⚠️  Process already stopped"
        fi
        
        rm -f "$PID_FILE"
        ;;
        
    status)
        if [ ! -f "$PID_FILE" ]; then
            echo "Status: ❌ Not running"
            exit 0
        fi
        
        PID=$(cat "$PID_FILE")
        
        if ps -p $PID > /dev/null 2>&1; then
            echo "╔════════════════════════════════════════════════════════════╗"
            echo "║     ✅ Traffic Generator Status: RUNNING                  ║"
            echo "╚════════════════════════════════════════════════════════════╝"
            echo ""
            echo "PID: $PID"
            echo "Runtime: $(ps -p $PID -o etime= | xargs)"
            echo ""
            echo "📊 Recent activity (last 10 lines):"
            tail -10 logs/traffic-generator.log 2>/dev/null || echo "  No logs yet"
            echo ""
            echo "📈 Total logs generated:"
            grep -c "Homepage accessed" logs/combined.log 2>/dev/null || echo "  0"
        else
            echo "Status: ❌ Not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    logs)
        echo "📊 Tailing traffic generator logs (Ctrl+C to stop)..."
        tail -f logs/traffic-generator.log
        ;;
        
    *)
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║     🎯 Traffic Generator Manager                          ║"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Usage: $0 {start|stop|status|restart|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start traffic generator in background"
        echo "  stop    - Stop traffic generator"
        echo "  status  - Check if running and show stats"
        echo "  restart - Restart traffic generator"
        echo "  logs    - Tail the traffic generator logs"
        echo ""
        exit 1
        ;;
esac

