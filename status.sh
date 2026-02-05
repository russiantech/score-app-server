#!/bin/bash
# status.sh - Check if the FastAPI app is running

echo "=== FastAPI App Status ==="
echo ""

if screen -list | grep -q "fastapi-studentscores"; then
    echo "✅ Status: RUNNING"
    screen -ls | grep fastapi-studentscores
else
    echo "❌ Status: NOT RUNNING"
fi

echo ""
echo "=== Port 8001 Status ==="
if netstat -tuln 2>/dev/null | grep -q ":8001 "; then
    echo "✅ Port 8001: LISTENING"
    netstat -tuln | grep :8001
elif ss -tuln 2>/dev/null | grep -q ":8001 "; then
    echo "✅ Port 8001: LISTENING"
    ss -tuln | grep :8001
else
    echo "❌ Port 8001: NOT LISTENING"
fi

echo ""
echo "=== Quick Test ==="
if curl -s http://localhost:8001 > /dev/null 2>&1; then
    echo "✅ API Response: OK"
    curl -s http://localhost:8001 | head -c 100
    echo "..."
else
    echo "❌ API Response: FAILED"
fi
