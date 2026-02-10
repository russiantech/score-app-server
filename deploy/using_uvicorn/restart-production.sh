#!/bin/bash
# restart-production.sh - Restart the application with zero-downtime strategy

APP_DIR="/home/simpdinr/api-studentscores.simplylovely.ng"
cd "$APP_DIR"

echo "=== Restarting FastAPI Application ==="
echo ""

# Stop current instance
echo "Step 1/2: Stopping current instance..."
./stop-production.sh

# Wait for clean shutdown
sleep 2

# Start new instance
echo ""
echo "Step 2/2: Starting new instance..."
./start-production.sh

echo ""
echo "✅ Restart complete"
