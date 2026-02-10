#!/bin/bash
# status.sh - Comprehensive status check for FastAPI app

echo "=== FastAPI App Status ==="
echo ""

# Check for screen session
if screen -list 2>/dev/null | grep -q "fastapi-studentscores"; then
    echo "✅ Screen Session: RUNNING"
    screen -ls | grep fastapi-studentscores
else
    echo "❌ Screen Session: NOT RUNNING"
fi

echo ""

# Check for ANY python main.py processes
if ps aux | grep -E "python.*main.py" | grep -v grep > /dev/null; then
    echo "✅ Python Processes: FOUND"
    ps aux | grep -E "python.*main.py" | grep -v grep | while read line; do
        PID=$(echo $line | awk '{print $2}')
        CMD=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        echo "   PID: $PID - $CMD"
    done
else
    echo "❌ Python Processes: NONE FOUND"
fi

echo ""
echo "=== Port 8001 Status ==="

if ss -tuln 2>/dev/null | grep -q ":8001 "; then
    echo "✅ Port 8001: LISTENING"
    ss -tulnp 2>/dev/null | grep :8001
elif netstat -tuln 2>/dev/null | grep -q ":8001 "; then
    echo "✅ Port 8001: LISTENING"
    netstat -tulnp 2>/dev/null | grep :8001
else
    echo "⚠️  Port 8001: Status unknown (no netstat/ss access)"
fi

echo ""
echo "=== API Response Test ==="

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001 2>/dev/null)

if [ "$RESPONSE" = "200" ]; then
    echo "✅ API Status: WORKING (HTTP $RESPONSE)"
    echo "Response preview:"
    curl -s http://localhost:8001 2>/dev/null | head -c 150
    echo "..."
elif [ -n "$RESPONSE" ]; then
    echo "⚠️  API Status: HTTP $RESPONSE"
else
    echo "❌ API Status: NOT RESPONDING"
fi

echo ""
echo "=== Log File ==="
if [ -f "app.log" ]; then
    echo "Last 5 log entries:"
    tail -5 app.log
else
    echo "No log file found"
fi
