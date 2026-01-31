@echo off
setlocal enabledelayedexpansion

echo 🔧 Running safe Alembic migration...

REM ------------------------------------------------------
REM 1. Ensure alembic.ini exists
REM ------------------------------------------------------
if not exist alembic.ini (
    echo ⚠ alembic.ini missing — initializing Alembic...
    alembic init alembic
)

REM ------------------------------------------------------
REM 2. Ensure alembic/ folder exists
REM ------------------------------------------------------
if not exist alembic (
    echo ⚠ alembic directory missing — initializing Alembic...
    alembic init alembic
)

REM ------------------------------------------------------
REM 3. Remove __pycache__ (non destructive)
REM ------------------------------------------------------
echo 🧹 Cleaning __pycache__ folders...
for /d /r %%i in (__pycache__) do (
    rd /s /q "%%i"
)

REM ------------------------------------------------------
REM 4. Autogenerate migration
REM ------------------------------------------------------
echo 📝 Autogenerating migration...
alembic revision --autogenerate -m "sync"
if errorlevel 1 (
    echo ❌ Autogenerate failed — fix model/database mismatch.
    exit /b 1
)

REM ------------------------------------------------------
REM 5. Apply upgrade
REM ------------------------------------------------------
echo 🚀 Applying migration...
alembic upgrade head
if errorlevel 1 (
    echo ❌ Migration failed — database remains unchanged.
    exit /b 1
)

echo ✅ Migration completed successfully!
pause
