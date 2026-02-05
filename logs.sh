#!/bin/bash
# logs.sh - View and follow application logs

cd "$(dirname "$0")"

echo "=== FastAPI Application Logs ==="
echo "Log file: $(pwd)/app.log"
echo ""
echo "Press Ctrl+C to stop watching"
echo "=========================================="
echo ""

# Follow logs with color highlighting for errors
tail -f app.log 2>/dev/null | while read line; do
    if echo "$line" | grep -q "ERROR"; then
        echo -e "\033[0;31m$line\033[0m"  # Red for errors
    elif echo "$line" | grep -q "WARNING"; then
        echo -e "\033[0;33m$line\033[0m"  # Yellow for warnings
    elif echo "$line" | grep -q "INFO"; then
        echo -e "\033[0;32m$line\033[0m"  # Green for info
    else
        echo "$line"
    fi
done

