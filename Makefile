PYTHON ?= python3

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -U pip && pip install -e '.[dev]'
	. .venv/bin/activate && python scripts/download_whisper_model.py --model small
	npm --prefix frontend install

setup-local-ai: setup
	. .venv/bin/activate && pip install -e '.[local-ai]'

frontend-build:
	npm --prefix frontend run build
	rm -rf backend/app/static
	mkdir -p backend/app/static
	cp -R frontend/dist/. backend/app/static/

dev-backend:
	. .venv/bin/activate && uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8765

dev-frontend:
	npm --prefix frontend run dev

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check backend apps scripts

check: lint test frontend-build
	. .venv/bin/activate && python -m compileall -q backend apps scripts
