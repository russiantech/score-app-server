#!/bin/bash
# install-autostart.sh - Configure automatic startup on server reboot

APP_DIR="/home/simpdinr/api-studentscores.simplylovely.ng"

echo "=== Installing Auto-Start Configuration ==="
echo ""

# Check if crontab exists
if ! crontab -l >/dev/null 2>&1; then
    echo "Creating new crontab..."
    touch /tmp/newcron
else
    echo "Backing up existing crontab..."
    crontab -l > /tmp/newcron
fi

# Check if entry already exists
if grep -q "api-studentscores.simplylovely.ng/start-production.sh" /tmp/newcron 2>/dev/null; then
    echo "⚠️  Auto-start entry already exists in crontab"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "api-studentscores"
    rm -f /tmp/newcron
    exit 0
fi

# Add auto-start entry
echo "" >> /tmp/newcron
echo "# Auto-start FastAPI application on server reboot" >> /tmp/newcron
echo "@reboot sleep 30 && cd $APP_DIR && ./start-production.sh >> $APP_DIR/startup.log 2>&1" >> /tmp/newcron
echo "" >> /tmp/newcron

# Add health check every 5 minutes (optional - ensures daemon is running)
echo "# Health check - restart if daemon died" >> /tmp/newcron
echo "*/5 * * * * cd $APP_DIR && ./healthcheck.sh >> $APP_DIR/healthcheck.log 2>&1" >> /tmp/newcron

# Install new crontab
crontab /tmp/newcron
rm -f /tmp/newcron

echo "✅ Auto-start configured successfully!"
echo ""
echo "Configuration:"
echo "  • Application will start automatically 30 seconds after server reboot"
echo "  • Health check runs every 5 minutes to ensure daemon is alive"
echo ""
echo "View cron jobs:"
echo "  crontab -l"
echo ""
echo "Remove auto-start:"
echo "  ./uninstall-autostart.sh"
echo ""
echo "Test startup manually:"
echo "  ./start-production.sh"
