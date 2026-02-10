#!/bin/bash
# logs-production.sh - View application logs with filtering options

APP_DIR="/home/simpdinr/api-studentscores.simplylovely.ng"
cd "$APP_DIR"

# Parse command line arguments
MODE="${1:-live}"
FILTER="${2:-all}"

show_help() {
    echo "Usage: ./logs-production.sh [MODE] [FILTER]"
    echo ""
    echo "Modes:"
    echo "  live     - Follow logs in real-time (default)"
    echo "  last     - Show last 50 lines"
    echo "  errors   - Show only errors"
    echo "  daemon   - Show daemon logs"
    echo ""
    echo "Filters (for live mode):"
    echo "  all      - All logs (default)"
    echo "  error    - Only errors"
    echo "  warning  - Only warnings"
    echo "  info     - Only info messages"
    echo ""
    echo "Examples:"
    echo "  ./logs-production.sh live error    # Follow only errors"
    echo "  ./logs-production.sh last           # Show last 50 lines"
    echo "  ./logs-production.sh errors         # Show all errors"
}

if [ "$MODE" = "help" ] || [ "$MODE" = "-h" ] || [ "$MODE" = "--help" ]; then
    show_help
    exit 0
fi

# Color codes
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

colorize() {
    while read line; do
        if echo "$line" | grep -qi "error"; then
            echo -e "${RED}$line${NC}"
        elif echo "$line" | grep -qi "warning"; then
            echo -e "${YELLOW}$line${NC}"
        elif echo "$line" | grep -qi "info"; then
            echo -e "${GREEN}$line${NC}"
        else
            echo "$line"
        fi
    done
}

filter_logs() {
    case "$FILTER" in
        error)
            grep -i "error"
            ;;
        warning)
            grep -i "warning"
            ;;
        info)
            grep -i "info"
            ;;
        *)
            cat
            ;;
    esac
}

case "$MODE" in
    live)
        echo "=== Live Application Logs (Press Ctrl+C to stop) ==="
        echo "Filter: $FILTER"
        echo "========================================"
        echo ""
        tail -f app.log 2>/dev/null | filter_logs | colorize
        ;;
    
    last)
        echo "=== Last 50 Log Lines ==="
        echo ""
        tail -50 app.log 2>/dev/null | colorize
        ;;
    
    errors)
        echo "=== All Errors ==="
        echo ""
        grep -i "error" app.log 2>/dev/null | colorize
        ;;
    
    daemon)
        echo "=== Daemon Logs ==="
        echo ""
        if [ -f "daemon.log" ]; then
            tail -50 daemon.log | colorize
        else
            echo "No daemon log found"
        fi
        ;;
    
    *)
        echo "Unknown mode: $MODE"
        echo ""
        show_help
        exit 1
        ;;
esac
