#!/bin/bash
# kill-all.sh - Kill ALL instances of the FastAPI app

echo "=== Searching for running FastAPI processes ==="

# Find all python processes running main.py
PIDS=$(ps aux | grep -E "python.*main.py" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No running processes found."
else
    echo "Found processes:"
    ps aux | grep -E "python.*main.py" | grep -v grep
    echo ""
    echo "Killing PIDs: $PIDS"
    kill -9 $PIDS 2>/dev/null
    echo "✅ All processes killed"
fi

# Also kill any screen sessions
if screen -list 2>/dev/null | grep -q "fastapi-studentscores"; then
    echo "Killing screen session..."
    screen -S fastapi-studentscores -X quit
    echo "✅ Screen session killed"
fi

echo ""
echo "=== Verification ==="
sleep 1

if ps aux | grep -E "python.*main.py" | grep -v grep > /dev/null; then
    echo "⚠️  WARNING: Some processes still running:"
    ps aux | grep -E "python.*main.py" | grep -v grep
else
    echo "✅ All processes stopped"
fi

# Test if API still responds
echo ""
if curl -s http://localhost:8001 > /dev/null 2>&1; then
    echo "⚠️  WARNING: API still responding on port 8001"
    echo "There may be hidden processes. Contact hosting support."
else
    echo "✅ Port 8001 is free"
fi
