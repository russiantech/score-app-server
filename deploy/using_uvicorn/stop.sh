#!/bin/bash
# stop.sh - Stop the FastAPI app

echo "Stopping FastAPI app..."

# Kill screen session if exists
if screen -list 2>/dev/null | grep -q "fastapi-studentscores"; then
    screen -S fastapi-studentscores -X quit
    echo "✅ Screen session terminated"
fi

# Kill any remaining python main.py processes
PIDS=$(ps aux | grep -E "python.*main.py" | grep -v grep | awk '{print $2}')
if [ -n "$PIDS" ]; then
    echo "Killing remaining processes: $PIDS"
    kill -9 $PIDS 2>/dev/null
    echo "✅ Processes killed"
fi

# Verify
sleep 1
if ps aux | grep -E "python.*main.py" | grep -v grep > /dev/null; then
    echo "⚠️  WARNING: Some processes may still be running"
    ps aux | grep -E "python.*main.py" | grep -v grep
else
    echo "✅ All processes stopped"
fi
