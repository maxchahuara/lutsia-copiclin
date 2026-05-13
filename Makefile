PYTHON ?= python3

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -e .[dev]

dev-backend:
	. .venv/bin/activate && uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8765

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check backend apps
