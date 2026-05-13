#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e '.[dev,local-ai]'
npm --prefix frontend install
npm --prefix frontend run build
rm -rf backend/app/static
mkdir -p backend/app/static
cp -R frontend/dist/. backend/app/static/
python scripts/check_runtime.py
cat <<'MSG'
Local AI Python packages are installed.
Model downloads are intentionally not automatic yet because they are large and should be selected by the physician/user.
Next: configure a faster-whisper model size in settings.
MSG
