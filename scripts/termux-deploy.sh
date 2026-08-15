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

# Python setup
PYTHON_CMD=${PYTHON_CMD:-python}
echo "[1/6] Python version: $($PYTHON_CMD --version 2>&1)"

# Install deps
echo "[2/6] Installing Python dependencies..."
$PYTHON_CMD -m pip install -q -r requirements.txt || pip install -q -r requirements.txt

# Verify imports
echo "[3/6] Verifying imports..."
$PYTHON_CMD -c "import api.core; import api.main; print('  All imports OK')"

# Run mocked tests
echo "[4/6] Running mocked test suite..."
$PYTHON_CMD -m pytest tests/ -v --ignore=tests/test_live_smoke.py --tb=short -W ignore::PendingDeprecationWarning

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
    echo "  PM2 not found. Starting with uvicorn..."
    echo "  Run: uvicorn api.main:app --host 0.0.0.0 --port 8000"
    echo "  Or install PM2: npm install -g pm2"
fi

echo ""
echo "=== Deploy Complete ==="
echo "Health check: curl http://localhost:8000/health"
echo "Docs:         curl http://localhost:8000/docs"
echo ""
