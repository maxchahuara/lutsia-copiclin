from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "LUTSIA CopiClin"
APP_AUTHOR = "LUTSIA"


def app_data_dir() -> Path:
    """Return the per-user data directory for the installed desktop app."""
    override = os.environ.get("LUTSIA_COPICLIN_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve(strict=False)
    return Path(user_data_dir(APP_NAME, APP_AUTHOR)).resolve(strict=False)


def consultations_dir() -> Path:
    return app_data_dir() / "consultations"


def codex_home_dir() -> Path:
    return app_data_dir() / "codex"


def whisper_models_dir() -> Path:
    return app_data_dir() / "whisper-models"
