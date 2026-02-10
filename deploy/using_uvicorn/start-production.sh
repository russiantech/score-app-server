#!/bin/bash
# start-production.sh - Start the FastAPI app with monitoring daemon

APP_DIR="/home/simpdinr/api-studentscores.simplylovely.ng"
cd "$APP_DIR"

echo "=== Starting FastAPI Application (Production Mode) ==="
echo ""

# Check if daemon is already running
if [ -f ".fastapi.pid" ]; then
    DAEMON_PID=$(cat .fastapi.pid)
    if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
        echo "❌ Application is already running (Daemon PID: $DAEMON_PID)"
        echo ""
        echo "Use './status-production.sh' to check status"
        echo "Use './stop-production.sh' to stop it"
        exit 1
    else
        echo "⚠️  Removing stale PID file"
        rm -f .fastapi.pid .app.pid
    fi
fi

# Remove any stop signals
rm -f .daemon.stop

# Kill any orphaned processes
echo "Cleaning up any orphaned processes..."
pkill -f "python.*main.py" 2>/dev/null
sleep 1

# Start daemon in background
echo "Starting monitoring daemon..."
nohup ./daemon.sh > /dev/null 2>&1 &
DAEMON_PID=$!

# Wait for startup
echo "Waiting for application to start..."
sleep 3

# Verify it started
if [ -f ".fastapi.pid" ] && ps -p "$(cat .fastapi.pid)" > /dev/null 2>&1; then
    echo ""
    echo "✅ Application started successfully!"
    echo ""
    echo "   Daemon PID: $(cat .fastapi.pid)"
    if [ -f ".app.pid" ]; then
        echo "   App PID: $(cat .app.pid)"
    fi
    echo ""
    
    # Test API
    sleep 2
    if curl -s -f http://localhost:8001/ > /dev/null 2>&1; then
        echo "✅ API health check: PASSED"
        echo ""
        echo "Your API is live at:"
        echo "   https://api-studentscores.simplylovely.ng/"
        echo "   https://api-studentscores.simplylovely.ng/docs"
    else
        echo "⚠️  API health check: FAILED (may still be starting)"
    fi
    
    echo ""
    echo "Management commands:"
    echo "   ./status-production.sh   - Check status"
    echo "   ./stop-production.sh     - Stop application"
    echo "   ./restart-production.sh  - Restart application"
    echo "   ./logs-production.sh     - View logs"
    echo ""
else
    echo ""
    echo "❌ Failed to start application"
    echo ""
    echo "Check logs:"
    echo "   tail -50 daemon.log"
    echo "   tail -50 app.log"
    exit 1
fi
