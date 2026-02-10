#!/bin/bash
# diagnose.sh - Check current Passenger configuration

echo "=== Checking Current Configuration ==="
echo ""

echo "1. .htaccess content:"
echo "----------------------------------------"
if [ -f ".htaccess" ]; then
    cat .htaccess
else
    echo "❌ .htaccess not found"
fi

echo ""
echo "2. passenger_wsgi.py content:"
echo "----------------------------------------"
if [ -f "passenger_wsgi.py" ]; then
    cat passenger_wsgi.py
else
    echo "❌ passenger_wsgi.py not found"
fi

echo ""
echo "3. Check if a2wsgi is installed:"
echo "----------------------------------------"
python -c "import a2wsgi; print('✅ a2wsgi installed:', a2wsgi.__version__)" 2>&1

echo ""
echo "4. Check if main.py imports correctly:"
echo "----------------------------------------"
python -c "from main import app; print('✅ main.py imports successfully')" 2>&1

echo ""
echo "5. Check for running processes:"
echo "----------------------------------------"
ps aux | grep -E "python.*main|passenger" | grep -v grep || echo "No processes found"

echo ""
echo "6. Recent app.log entries:"
echo "----------------------------------------"
if [ -f "app.log" ]; then
    tail -10 app.log
else
    echo "No app.log found"
fi

echo ""
echo "7. Recent stderr.log entries:"
echo "----------------------------------------"
if [ -f "stderr.log" ]; then
    tail -10 stderr.log
else
    echo "No stderr.log found"
fi
