#!/bin/bash
# daemon.sh - Production daemon that keeps FastAPI running with auto-restart

APP_DIR="/home/simpdinr/api-studentscores.simplylovely.ng"
VENV_PYTHON="/home/simpdinr/virtualenv/api-studentscores.simplylovely.ng/3.13/bin/python"
PID_FILE="$APP_DIR/.fastapi.pid"
LOG_FILE="$APP_DIR/daemon.log"
MAX_RESTART_ATTEMPTS=5
RESTART_DELAY=5

cd "$APP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if daemon is already running
if [ -f "$PID_FILE" ]; then
    DAEMON_PID=$(cat "$PID_FILE")
    if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
        log "ERROR: Daemon already running (PID: $DAEMON_PID)"
        exit 1
    else
        log "WARNING: Stale PID file found, removing"
        rm -f "$PID_FILE"
    fi
fi

# Save daemon PID
echo $$ > "$PID_FILE"
log "INFO: Daemon started (PID: $$)"

# Function to start the app
start_app() {
    log "INFO: Starting FastAPI application..."
    
    # Kill any existing python main.py processes
    pkill -f "python.*main.py" 2>/dev/null
    sleep 1
    
    # Start the app
    nohup "$VENV_PYTHON" "$APP_DIR/main.py" >> "$LOG_FILE" 2>&1 &
    APP_PID=$!
    
    log "INFO: Application started (PID: $APP_PID)"
    echo $APP_PID > "$APP_DIR/.app.pid"
    
    return $APP_PID
}

# Function to check if app is healthy
is_healthy() {
    curl -s -f http://localhost:8001/ > /dev/null 2>&1
    return $?
}

# Function to get app PID
get_app_pid() {
    if [ -f "$APP_DIR/.app.pid" ]; then
        cat "$APP_DIR/.app.pid"
    else
        echo ""
    fi
}

# Main monitoring loop
restart_count=0
start_app

log "INFO: Entering monitoring loop (checking every 10 seconds)"

while true; do
    sleep 10
    
    APP_PID=$(get_app_pid)
    
    # Check if process is running
    if [ -n "$APP_PID" ] && ps -p "$APP_PID" > /dev/null 2>&1; then
        # Process exists, check health
        if is_healthy; then
            # All good, reset restart counter
            restart_count=0
        else
            log "WARNING: Health check failed (PID $APP_PID still running but not responding)"
            # Give it a few more chances before restarting
        fi
    else
        # Process died
        log "ERROR: Application process died (PID: $APP_PID)"
        
        if [ $restart_count -ge $MAX_RESTART_ATTEMPTS ]; then
            log "CRITICAL: Max restart attempts ($MAX_RESTART_ATTEMPTS) reached. Stopping daemon."
            rm -f "$PID_FILE"
            exit 1
        fi
        
        restart_count=$((restart_count + 1))
        log "INFO: Restart attempt $restart_count/$MAX_RESTART_ATTEMPTS (waiting ${RESTART_DELAY}s)"
        sleep $RESTART_DELAY
        
        start_app
    fi
    
    # Check if daemon should stop (via .daemon.stop file)
    if [ -f "$APP_DIR/.daemon.stop" ]; then
        log "INFO: Stop signal received, shutting down gracefully"
        APP_PID=$(get_app_pid)
        if [ -n "$APP_PID" ]; then
            kill "$APP_PID" 2>/dev/null
        fi
        rm -f "$PID_FILE" "$APP_DIR/.app.pid" "$APP_DIR/.daemon.stop"
        log "INFO: Daemon stopped"
        exit 0
    fi
done
