#!/bin/bash
# stop-production.sh - Stop the FastAPI application gracefully

APP_DIR="/home/simpdinr/api-studentscores.simplylovely.ng"
cd "$APP_DIR"

echo "=== Stopping FastAPI Application ==="
echo ""

if [ ! -f ".fastapi.pid" ]; then
    echo "⚠️  No daemon PID file found"
    
    # Check for orphaned processes anyway
    if ps aux | grep -E "python.*main.py" | grep -v grep > /dev/null; then
        echo "Found orphaned processes, cleaning up..."
        pkill -f "python.*main.py"
        sleep 1
        echo "✅ Orphaned processes killed"
    else
        echo "Application is not running"
    fi
    exit 0
fi

DAEMON_PID=$(cat .fastapi.pid)

if ! ps -p "$DAEMON_PID" > /dev/null 2>&1; then
    echo "⚠️  Daemon not running (stale PID file)"
    rm -f .fastapi.pid .app.pid
    
    # Clean up any orphaned processes
    pkill -f "python.*main.py" 2>/dev/null
    echo "✅ Cleanup complete"
    exit 0
fi

# Signal daemon to stop gracefully
echo "Sending stop signal to daemon (PID: $DAEMON_PID)..."
touch .daemon.stop

# Wait for graceful shutdown (max 15 seconds)
for i in {1..15}; do
    if ! ps -p "$DAEMON_PID" > /dev/null 2>&1; then
        echo "✅ Application stopped gracefully"
        rm -f .fastapi.pid .app.pid .daemon.stop
        exit 0
    fi
    sleep 1
done

# Force kill if graceful shutdown failed
echo "⚠️  Graceful shutdown timeout, force killing..."
kill -9 "$DAEMON_PID" 2>/dev/null

# Kill app process too
if [ -f ".app.pid" ]; then
    APP_PID=$(cat .app.pid)
    kill -9 "$APP_PID" 2>/dev/null
fi

# Clean up any remaining processes
pkill -9 -f "python.*main.py" 2>/dev/null

rm -f .fastapi.pid .app.pid .daemon.stop

echo "✅ Application force stopped"
