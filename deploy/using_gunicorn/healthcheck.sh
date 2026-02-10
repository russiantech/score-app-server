#!/bin/bash
# healthcheck.sh - Automated health check that restarts daemon if needed

APP_DIR="/home/simpdinr/api-studentscores.simplylovely.ng"
cd "$APP_DIR"

# Silent mode - only output on errors
LOG_FILE="$APP_DIR/healthcheck.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if daemon is running
if [ -f ".fastapi.pid" ]; then
    DAEMON_PID=$(cat .fastapi.pid)
    if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
        # Daemon is running, check API health
        if curl -s -f http://localhost:8001/ > /dev/null 2>&1; then
            # Everything is healthy, exit silently
            exit 0
        else
            log "WARNING: API not responding, but daemon is running (PID: $DAEMON_PID)"
            # Daemon should auto-restart the app, give it a chance
            exit 0
        fi
    else
        log "ERROR: Daemon died (stale PID: $DAEMON_PID)"
    fi
else
    log "ERROR: Daemon not running (no PID file)"
fi

# Daemon is not running, restart it
log "INFO: Restarting daemon..."

# Clean up
rm -f .fastapi.pid .app.pid .daemon.stop
pkill -f "python.*main.py" 2>/dev/null
sleep 2

# Start daemon
nohup "$APP_DIR/daemon.sh" > /dev/null 2>&1 &

sleep 5

# Verify it started
if [ -f ".fastapi.pid" ] && ps -p "$(cat .fastapi.pid)" > /dev/null 2>&1; then
    if curl -s -f http://localhost:8001/ > /dev/null 2>&1; then
        log "INFO: Daemon restarted successfully"
    else
        log "ERROR: Daemon started but API not responding"
    fi
else
    log "CRITICAL: Failed to restart daemon"
fi
