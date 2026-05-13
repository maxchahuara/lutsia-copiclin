#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

from app.services.whisper_models import download_whisper_model, valid_model_ids


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download and verify a local faster-whisper model."
    )
    parser.add_argument("--model", default="small")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    args = parser.parse_args()

    if os.environ.get("LUTSIA_COPICLIN_SKIP_MODEL_DOWNLOAD") == "1":
        print("Skipping Whisper model download because LUTSIA_COPICLIN_SKIP_MODEL_DOWNLOAD=1")
        return 0

    if args.model not in valid_model_ids():
        print(
            f"Unsupported model '{args.model}'. Available: {', '.join(sorted(valid_model_ids()))}",
            file=sys.stderr,
        )
        return 2

    print(f"Downloading/verifying local Whisper model '{args.model}'")
    download_whisper_model(args.model)
    print("Local Whisper model is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
