#!/bin/bash
# Termux deployment script for Agentic Harness Integration Layer
# Run from project root on Android/Termux

set -e

echo "=== Agentic Harness Termux Deploy ==="
echo ""

# Check Termux
if [ -z "$TERMUX_VERSION" ]; then
    echo "Warning: Not running in Termux. Continuing anyway..."
fi

# Python setup — prefer repo .venv if present, else create it
PYTHON_CMD=${PYTHON_CMD:-python}
if [ -x .venv/bin/python ]; then
    PYTHON_CMD=.venv/bin/python
    echo "[1/6] Using repo venv: $($PYTHON_CMD --version 2>&1)"
else
    echo "[1/6] Python version: $($PYTHON_CMD --version 2>&1)"
    echo "  Creating .venv..."
    $PYTHON_CMD -m venv .venv
    PYTHON_CMD=.venv/bin/python
fi
PIP_CMD=${PYTHON_CMD%/*}/pip

# Install deps
echo "[2/6] Installing Python dependencies..."
$PIP_CMD install -q -r requirements.txt 2>&1 | tail -1

# Verify imports
echo "[3/6] Verifying imports..."
$PYTHON_CMD -c "import api.core; import api.main; print('  All imports OK')"

# Run mocked tests
echo "[4/6] Running mocked test suite..."
$PYTHON_CMD -m pytest tests/ -q --ignore=tests/test_live_smoke.py -W ignore::PendingDeprecationWarning 2>&1 | tail -2

# Check for .env
echo "[5/6] Checking environment..."
if [ ! -f .env ]; then
    echo "  .env not found. Copying from .env.example..."
    cp .env.example .env
    echo "  Please edit .env with your actual API keys before running live tests."
fi

# Start with PM2 if available, else uvicorn directly
echo "[6/6] Starting API server..."
if command -v pm2 &> /dev/null; then
    echo "  Using PM2..."
    pm2 delete harness-api 2>/dev/null || true
    pm2 start "uvicorn api.main:app --host 0.0.0.0 --port 8000" --name harness-api
    pm2 save
    echo "  API running via PM2. Check: pm2 logs harness-api"
else
    echo "  PM2 not found. Starting with nohup uvicorn..."
    nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
    echo "  Started uvicorn (PID $!) -> uvicorn.log"
fi

echo ""
echo "=== Health check ==="
for i in $(seq 1 20); do
    sleep 1
    if curl -fsS http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "  OK: http://127.0.0.1:8000/health"
        echo ""
        echo "=== Deploy Complete ==="
        exit 0
    fi
done
echo "  ERROR: health check timed out. See uvicorn.log / pm2 logs harness-api"
exit 1
