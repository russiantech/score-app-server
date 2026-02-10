#!/bin/bash
# start.sh - Start the FastAPI app in background

cd "$(dirname "$0")"

# Check if screen session exists
if screen -list 2>/dev/null | grep -q "fastapi-studentscores"; then
    echo "⚠️  Screen session already exists!"
    echo "Use ./stop.sh to stop it first, or ./restart.sh to restart."
    exit 1
fi

# Check if ANY python main.py process is running
if ps aux | grep -E "python.*main.py" | grep -v grep > /dev/null; then
    echo "⚠️  Found existing python main.py processes:"
    ps aux | grep -E "python.*main.py" | grep -v grep
    echo ""
    echo "Use ./kill-all.sh to stop all processes first."
    exit 1
fi

# Start in screen session
screen -dmS fastapi-studentscores bash -c '
  source /home/simpdinr/virtualenv/api-studentscores.simplylovely.ng/3.13/bin/activate && 
  cd /home/simpdinr/api-studentscores.simplylovely.ng && 
  python main.py
'

# Wait a moment for startup
sleep 2

# Verify it started
if screen -list 2>/dev/null | grep -q "fastapi-studentscores"; then
    echo "✅ FastAPI app started successfully"
    echo ""
    echo "Commands:"
    echo "  ./status.sh    - Check status"
    echo "  ./logs.sh      - Watch logs in real-time"
    echo "  ./stop.sh      - Stop the app"
    echo "  ./restart.sh   - Restart the app"
    echo ""
    
    # Quick test
    sleep 1
    if curl -s http://localhost:8001 > /dev/null 2>&1; then
        echo "✅ API is responding on http://localhost:8001"
    else
        echo "⚠️  API started but not responding yet (may take a few seconds)"
    fi
else
    echo "❌ Failed to start app"
    echo "Check logs: tail -20 app.log"
fi
