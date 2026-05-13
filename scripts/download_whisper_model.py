#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

from app.paths import whisper_models_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and verify a local faster-whisper model.")
    parser.add_argument("--model", default=os.environ.get("LUTSIA_COPICLIN_WHISPER_MODEL", "small"))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    args = parser.parse_args()

    if os.environ.get("LUTSIA_COPICLIN_SKIP_MODEL_DOWNLOAD") == "1":
        print("Skipping Whisper model download because LUTSIA_COPICLIN_SKIP_MODEL_DOWNLOAD=1")
        return 0

    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as exc:
        print("faster-whisper is not installed. Run: pip install -e '.[dev]'", file=sys.stderr)
        raise SystemExit(2) from exc

    target = whisper_models_dir() / args.model
    target.mkdir(parents=True, exist_ok=True)
    print(f"Downloading/verifying local Whisper model '{args.model}' in {target}")
    WhisperModel(args.model, device=args.device, compute_type=args.compute_type, download_root=str(target))
    print("Local Whisper model is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
