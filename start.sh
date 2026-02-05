#!/bin/bash
# start.sh - Start the FastAPI app in background

cd "$(dirname "$0")"

# Check if already running
if screen -list | grep -q "fastapi-studentscores"; then
    echo "App is already running!"
    echo "Use ./stop.sh to stop it first."
    exit 1
fi

# Start in screen session
screen -dmS fastapi-studentscores bash -c '
  source /home/simpdinr/virtualenv/api-studentscores.simplylovely.ng/3.13/bin/activate && 
  cd /home/simpdinr/api-studentscores.simplylovely.ng && 
  python main.py
'

echo "✅ FastAPI app started in background"
echo "Check status with: screen -ls"
echo "View logs with: tail -f app.log"
echo "Stop with: ./stop.sh"
