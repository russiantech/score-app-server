#!/bin/bash
# stop.sh - Stop the FastAPI app

if ! screen -list | grep -q "fastapi-studentscores"; then
    echo "App is not running."
    exit 0
fi

screen -S fastapi-studentscores -X quit
echo "✅ FastAPI app stopped"
