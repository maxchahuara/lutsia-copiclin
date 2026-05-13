#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e '.[dev]'
npm --prefix frontend install
npm --prefix frontend run build
rm -rf backend/app/static
mkdir -p backend/app/static
cp -R frontend/dist/. backend/app/static/
python scripts/check_runtime.py
pytest -q
