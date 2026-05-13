#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e '.[dev,local-ai]'
python scripts/check_runtime.py
cat <<'MSG'
Local AI Python packages are installed.
Model downloads are intentionally not automatic yet because they are large and should be selected by the physician/user.
Next: configure a faster-whisper model size in settings, or install Ollama from official packages for local LLM use.
MSG
