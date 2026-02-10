#!/bin/bash
# uninstall-autostart.sh - Remove auto-start configuration

echo "=== Removing Auto-Start Configuration ==="
echo ""

if ! crontab -l >/dev/null 2>&1; then
    echo "No crontab found, nothing to remove"
    exit 0
fi

# Backup existing crontab
crontab -l > /tmp/oldcron

# Remove FastAPI related entries
grep -v "api-studentscores.simplylovely.ng" /tmp/oldcron > /tmp/newcron

# Install cleaned crontab
crontab /tmp/newcron
rm -f /tmp/oldcron /tmp/newcron

echo "✅ Auto-start configuration removed"
echo ""
echo "The application will no longer start automatically on server reboot"
echo ""
echo "To re-enable, run:"
echo "  ./install-autostart.sh"
