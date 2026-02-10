#!/bin/bash
# restart.sh - Restart the FastAPI app

cd "$(dirname "$0")"

echo "Stopping app..."
./stop.sh

echo "Waiting 2 seconds..."
sleep 2

echo "Starting app..."
./start.sh
