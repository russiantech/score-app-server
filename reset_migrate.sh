#!/bin/bash
set -e

echo "🔧 Running safe Alembic migration..."

# ------------------------------------------------------
# 1. Ensure alembic.ini exists
# ------------------------------------------------------
if [ ! -f "alembic.ini" ]; then
    echo "⚠ alembic.ini not found — initializing Alembic..."
    alembic init alembic
fi

# ------------------------------------------------------
# 2. Ensure alembic/ folder exists
# ------------------------------------------------------
if [ ! -d "alembic" ]; then
    echo "⚠ alembic directory missing — creating new Alembic env..."
    alembic init alembic
fi

# ------------------------------------------------------
# 3. Remove __pycache__ (non-destructive)
# ------------------------------------------------------
echo "🧹 Cleaning __pycache__..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# ------------------------------------------------------
# 4. Autogenerate migration
# ------------------------------------------------------
echo "📝 Autogenerating migration..."
if ! alembic revision --autogenerate -m "sync"; then
    echo "❌ Autogenerate failed — fix model/database mismatch."
    exit 1
fi

# ------------------------------------------------------
# 5. Apply upgrade
# ------------------------------------------------------
echo "🚀 Applying migration..."
if ! alembic upgrade head; then
    echo "❌ Migration failed — database remains unchanged."
    exit 1
fi

echo "✅ Migration completed successfully!"

