#!/bin/bash
# status-production.sh - Comprehensive production status check

APP_DIR="/home/simpdinr/api-studentscores.simplylovely.ng"
cd "$APP_DIR"

echo "=== FastAPI Production Status ==="
echo ""

# Check daemon
if [ -f ".fastapi.pid" ]; then
    DAEMON_PID=$(cat .fastapi.pid)
    if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
        echo "✅ Monitoring Daemon: RUNNING (PID: $DAEMON_PID)"
        
        # Get daemon uptime
        DAEMON_START=$(ps -p "$DAEMON_PID" -o lstart= 2>/dev/null)
        if [ -n "$DAEMON_START" ]; then
            echo "   Started: $DAEMON_START"
        fi
    else
        echo "❌ Monitoring Daemon: NOT RUNNING (stale PID)"
    fi
else
    echo "❌ Monitoring Daemon: NOT RUNNING"
fi

echo ""

# Check app process
if [ -f ".app.pid" ]; then
    APP_PID=$(cat .app.pid)
    if ps -p "$APP_PID" > /dev/null 2>&1; then
        echo "✅ Application Process: RUNNING (PID: $APP_PID)"
        
        # Get app uptime
        APP_START=$(ps -p "$APP_PID" -o lstart= 2>/dev/null)
        if [ -n "$APP_START" ]; then
            echo "   Started: $APP_START"
        fi
        
        # Get memory usage
        MEM=$(ps -p "$APP_PID" -o rss= 2>/dev/null)
        if [ -n "$MEM" ]; then
            MEM_MB=$((MEM / 1024))
            echo "   Memory: ${MEM_MB} MB"
        fi
    else
        echo "❌ Application Process: NOT RUNNING (stale PID)"
    fi
else
    echo "❌ Application Process: NOT RUNNING"
fi

echo ""
echo "=== API Health Check ==="

# Test API response
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/ 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health Status: HEALTHY (HTTP $HTTP_CODE)"
    
    # Get response preview
    RESPONSE=$(curl -s http://localhost:8001/ 2>/dev/null)
    VERSION=$(echo "$RESPONSE" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$VERSION" ]; then
        echo "   API Version: $VERSION"
    fi
    
    # Test response time
    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" http://localhost:8001/ 2>/dev/null)
    echo "   Response Time: ${RESPONSE_TIME}s"
    
elif [ -n "$HTTP_CODE" ]; then
    echo "⚠️  Health Status: DEGRADED (HTTP $HTTP_CODE)"
else
    echo "❌ Health Status: UNREACHABLE"
fi

echo ""
echo "=== Recent Activity ==="

# Check daemon log
if [ -f "daemon.log" ]; then
    echo "Daemon log (last 5 entries):"
    tail -5 daemon.log | sed 's/^/   /'
else
    echo "No daemon log found"
fi

echo ""

# Check app log
if [ -f "app.log" ]; then
    echo "Application log (last 3 entries):"
    tail -3 app.log | sed 's/^/   /'
    
    # Count recent errors
    ERROR_COUNT=$(grep -c "ERROR" app.log 2>/dev/null || echo 0)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo ""
        echo "⚠️  Total errors in log: $ERROR_COUNT"
        echo "   View with: grep ERROR app.log"
    fi
else
    echo "No application log found"
fi

echo ""
echo "=== Endpoints ==="
echo "   Public: https://api-studentscores.simplylovely.ng/"
echo "   Docs:   https://api-studentscores.simplylovely.ng/docs"
echo "   Local:  http://localhost:8001/"

echo ""
