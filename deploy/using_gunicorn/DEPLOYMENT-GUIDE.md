# FastAPI Production Deployment Guide

## 📁 File Structure

```
/home/simpdinr/api-studentscores.simplylovely.ng/
├── main.py                    # Your FastAPI application
├── app/                       # Application code
├── .htaccess                  # Apache configuration
│
├── daemon.sh                  # Monitoring daemon (auto-restart on crash)
├── start-production.sh        # Start application
├── stop-production.sh         # Stop application
├── restart-production.sh      # Restart application
├── status-production.sh       # Check status
├── logs-production.sh         # View logs
├── healthcheck.sh            # Automated health monitoring
├── install-autostart.sh      # Enable auto-start on reboot
├── uninstall-autostart.sh    # Disable auto-start
├── rotate-logs.sh            # Rotate log files
│
├── .fastapi.pid              # Daemon process ID
├── .app.pid                  # Application process ID
├── app.log                   # Application logs
├── daemon.log                # Daemon monitoring logs
├── healthcheck.log           # Health check logs
└── startup.log               # Auto-start logs
```

## 🚀 Initial Setup

### 1. Upload all scripts to your server

```bash
cd /home/simpdinr/api-studentscores.simplylovely.ng
# Upload the scripts
```

### 2. Make scripts executable

```bash
chmod +x daemon.sh
chmod +x start-production.sh
chmod +x stop-production.sh
chmod +x restart-production.sh
chmod +x status-production.sh
chmod +x logs-production.sh
chmod +x healthcheck.sh
chmod +x install-autostart.sh
chmod +x uninstall-autostart.sh
chmod +x rotate-logs.sh
```

### 3. Update .htaccess

```apache
# Disable Passenger (we run uvicorn directly)
PassengerEnabled off

# Enable rewrite
RewriteEngine On
Script
# Force HTTPS
RewriteCond %{HTTPS} !=on
RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]

# Proxy to local uvicorn
RewriteCond %{REQUEST_URI} !^/\.well-known/
RewriteRule ^(.*)$ http://127.0.0.1:8001/$1 [P,L]
```

### 4. Kill any existing processes

```bash
./stop-production.sh
pkill -f "python.*main.py"
```

### 5. Start the application

```bash
./start-production.sh
```

### 6. Install auto-start on reboot

```bash
./install-autostart.sh
```

## 📊 Management Commands

| Command | Description |
|---------|-------------|
| `./start-production.sh` | Start application with monitoring |
| `./stop-production.sh` | Stop application gracefully |
| `./restart-production.sh` | Restart application |
| `./status-production.sh` | Show detailed status |
| `./logs-production.sh live` | Watch logs in real-time |
| `./logs-production.sh errors` | Show all errors |
| `./logs-production.sh last` | Show last 50 lines |

## 🔧 Features

###  Auto-Restart on Crash
- Daemon monitors the app every 10 seconds
- Automatically restarts if process dies
- Maximum 5 restart attempts with delays

###  Auto-Start on Server Reboot
- Starts automatically 30 seconds after reboot
- Health check runs every 5 minutes via cron

###  Health Monitoring
- API health checks via curl
- Process monitoring
- Automatic recovery

###  Log Management
- Colored output (red=errors, yellow=warnings, green=info)
- Multiple log files (app, daemon, health, startup)
- Automatic rotation when logs exceed 50MB

## 🐛 Troubleshooting

### Application won't start

```bash
# Check logs
./logs-production.sh last

# Check daemon log
tail -50 daemon.log

# Manual start
./stop-production.sh
sleep 2
./start-production.sh
```

### Application not responding

```bash
# Check status
./status-production.sh

# Test API
curl http://localhost:8001/

# Restart
./restart-production.sh
```

### View errors

```bash
# Watch errors in real-time
./logs-production.sh live error

# List all errors
grep -i error app.log | tail -20
```

## 📝 Logs Location

- **app.log** - FastAPI application logs
- **daemon.log** - Daemon monitoring logs
- **healthcheck.log** - Automated health check logs
- **startup.log** - Auto-start logs from cron

## ⚙️ Configuration

Edit `daemon.sh` to customize:
- `MAX_RESTART_ATTEMPTS=5` - Max restart tries
- `RESTART_DELAY=5` - Seconds between restarts

Edit `rotate-logs.sh` to customize:
- `MAX_SIZE_MB=50` - Log size before rotation
- `KEEP_BACKUPS=5` - Number of backup files

## 🔄 Deployment Workflow

### Deploy new code:

```bash
# 1. Upload new code
cd /home/simpdinr/api-studentscores.simplylovely.ng

# 2. Restart application
./restart-production.sh

# 3. Verify it's running
./status-production.sh

# 4. Watch for errors
./logs-production.sh live error
```

## 🌐 Access Points

- **Public API**: https://api-studentscores.simplylovely.ng/
- **API Docs**: https://api-studentscores.simplylovely.ng/docs
- **ReDoc**: https://api-studentscores.simplylovely.ng/redoc
- **Local**: http://localhost:8001/

##  Verification Checklist

After deployment:

- [ ] `./status-production.sh` shows all 
- [ ] https://api-studentscores.simplylovely.ng/ returns JSON
- [ ] https://api-studentscores.simplylovely.ng/docs loads
- [ ] `crontab -l` shows auto-start entry
- [ ] Logs are being written to app.log
