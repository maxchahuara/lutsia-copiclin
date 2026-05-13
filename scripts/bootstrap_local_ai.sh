#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e '.[dev,local-ai]'
python scripts/download_whisper_model.py --model "${LUTSIA_COPICLIN_WHISPER_MODEL:-small}"
npm --prefix frontend install
npm --prefix frontend run build
rm -rf backend/app/static
mkdir -p backend/app/static
cp -R frontend/dist/. backend/app/static/
python scripts/check_runtime.py
cat <<'MSG'
Local Whisper packages and the default local model are installed.
Transcription is local-only; CopiClin does not send consultation audio to transcription APIs.
MSG
