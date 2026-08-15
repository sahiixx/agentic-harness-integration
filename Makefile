.PHONY: install test test-live lint format docker-up docker-dev clean

PYTHON := /usr/local/bin/python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest

install:
	$(PIP) install -r requirements.txt

test:
	$(PYTEST) tests/ -v --ignore=tests/test_live_smoke.py --tb=short -W ignore::PendingDeprecationWarning

test-live:
	$(PYTEST) tests/test_live_smoke.py -v --tb=short

test-all:
	$(PYTEST) tests/ -v --tb=short -W ignore::PendingDeprecationWarning

test-count:
	@$(PYTEST) tests/ --ignore=tests/test_live_smoke.py --collect-only -q | tail -1

docker-up:
	docker-compose up --build

docker-dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

docker-down:
	docker-compose down

docker-config:
	docker-compose config

lint:
	$(PYTHON) -m py_compile api/core.py
	$(PYTHON) -m py_compile api/main.py
	$(PYTHON) -m py_compile api/nexus_bridge.py
	$(PYTHON) -m py_compile api/gapclaw_bridge.py
	$(PYTHON) -m py_compile api/sara_bridge.py
	$(PYTHON) -m py_compile api/gapsolver_bridge.py
	$(PYTHON) -m py_compile api/db.py
	$(PYTHON) -m py_compile api/redis_client.py
	$(PYTHON) -m py_compile api/tools/apollo.py
	$(PYTHON) -m py_compile api/tools/brightdata.py
	$(PYTHON) -m py_compile api/tools/wati.py

format:
	@echo "Run black/isort manually if installed"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/

termux-deploy:
	@echo "Deploying to Termux..."
	bash scripts/termux-deploy.sh
