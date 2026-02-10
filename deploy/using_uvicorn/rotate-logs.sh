#!/bin/bash
# rotate-logs.sh - Rotate log files to prevent disk space issues

APP_DIR="/home/simpdinr/api-studentscores.simplylovely.ng"
cd "$APP_DIR"

MAX_SIZE_MB=50  # Rotate when log exceeds this size
KEEP_BACKUPS=5  # Keep this many backup files

rotate_log() {
    local logfile="$1"
    local maxsize=$((MAX_SIZE_MB * 1024 * 1024))  # Convert to bytes
    
    if [ ! -f "$logfile" ]; then
        return
    fi
    
    local filesize=$(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null)
    
    if [ -z "$filesize" ]; then
        return
    fi
    
    if [ "$filesize" -gt "$maxsize" ]; then
        echo "Rotating $logfile (size: $((filesize / 1024 / 1024))MB)"
        
        # Shift existing backups
        for i in $(seq $((KEEP_BACKUPS - 1)) -1 1); do
            if [ -f "${logfile}.${i}" ]; then
                mv "${logfile}.${i}" "${logfile}.$((i + 1))"
            fi
        done
        
        # Create new backup
        mv "$logfile" "${logfile}.1"
        touch "$logfile"
        
        # Remove old backups
        for i in $(seq $((KEEP_BACKUPS + 1)) 10); do
            rm -f "${logfile}.${i}"
        done
        
        echo "✅ Rotated $logfile"
    fi
}

echo "=== Log Rotation ==="
echo "Checking logs..."
echo ""

rotate_log "app.log"
rotate_log "daemon.log"
rotate_log "healthcheck.log"
rotate_log "startup.log"

echo ""
echo "Done. Logs will be rotated when they exceed ${MAX_SIZE_MB}MB"
