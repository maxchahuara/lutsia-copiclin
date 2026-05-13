#!/usr/bin/env bash
set -euo pipefail
uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8765
