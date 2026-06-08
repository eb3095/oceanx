PYTHON ?= python3
VENV ?= .venv
PIP = $(VENV)/bin/pip
PY = $(VENV)/bin/python
PACKAGE = oceanx

.PHONY: help venv dev-install dev_install install run format format-check test uninstall deploy clean

help:
	@echo "OceanX development targets:"
	@echo "  make venv          Create virtualenv"
	@echo "  make dev-install   Editable install with dev deps"
	@echo "  make install       Install oceanx CLI into venv"
	@echo "  make run           Run from source via start.sh"
	@echo "  make format        Format code with black"
	@echo "  make format-check  Verify formatting (CI)"
	@echo "  make test          Run unit tests"
	@echo "  make uninstall     Uninstall package from venv"
	@echo "  make deploy        Placeholder deploy target"
	@echo "  make clean         Remove build artifacts"

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -U pip

dev-install: venv
	$(PIP) install -e ".[dev]"

dev_install: dev-install

install: venv
	$(PIP) install -e .

run:
	./start.sh

format:
	$(PY) -m black $(PACKAGE) tests

format-check:
	$(PY) -m black --check $(PACKAGE) tests

test:
	$(PY) -m pytest tests/ -v

uninstall:
	$(PIP) uninstall -y oceanx || true

deploy:
	@echo "No deploy target configured for oceanx."

clean:
	rm -rf build dist *.egg-info .pytest_cache
