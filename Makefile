PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
RUFF ?= $(PYTHON) -m ruff

SRC_PATHS = app tests scripts alembic

.PHONY: install lint format test ci migrate seed

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

lint:
	$(RUFF) check $(SRC_PATHS)

format:
	$(RUFF) format $(SRC_PATHS)

test:
	$(PYTHON) -m pytest

migrate:
	alembic upgrade head

seed:
	$(PYTHON) -m scripts.seed_data

ci: lint test
