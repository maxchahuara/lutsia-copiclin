from __future__ import annotations

import importlib.util
import shutil

from app.paths import whisper_models_dir
from dataclasses import dataclass, asdict

from app.services.codex_account import CodexAccountProvider


@dataclass
class Capability:
    id: str
    ok: bool
    required_for: str
    detail: str
    install_hint: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def codex_login_status() -> tuple[bool, str]:
    status = CodexAccountProvider().status()
    return status.logged_in, f"{status.detail} (CODEX_HOME={status.codex_home})"


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def check_capabilities() -> list[Capability]:
    caps: list[Capability] = []
    caps.append(Capability(
        id="ffmpeg-system",
        ok=shutil.which("ffmpeg") is not None,
        required_for="audio conversion fallback",
        detail=shutil.which("ffmpeg") or "system ffmpeg not found; packaged imageio-ffmpeg may still work",
        install_hint="Install ffmpeg or rely on bundled imageio-ffmpeg in packaged builds.",
    ))
    caps.append(Capability(
        id="ffmpeg-bundled",
        ok=module_available("imageio_ffmpeg"),
        required_for="packaged audio conversion",
        detail="Python imageio-ffmpeg package availability",
        install_hint="pip install imageio-ffmpeg",
    ))
    caps.append(Capability(
        id="keyring",
        ok=module_available("keyring"),
        required_for="secure account/API secret storage",
        detail="OS keychain access via keyring",
        install_hint="pip install keyring",
    ))
    faster_whisper_ok = module_available("faster_whisper")
    caps.append(Capability(
        id="faster-whisper",
        ok=faster_whisper_ok,
        required_for="local Whisper transcription",
        detail="Local Whisper backend package",
        install_hint="pip install -e .[dev]",
    ))
    default_model_dir = whisper_models_dir() / "small"
    model_ready = default_model_dir.exists() and any(default_model_dir.iterdir())
    caps.append(Capability(
        id="whisper-model-small",
        ok=model_ready,
        required_for="offline local Whisper transcription",
        detail=str(default_model_dir) if model_ready else f"model not found at {default_model_dir}",
        install_hint="python scripts/download_whisper_model.py --model small",
    ))
    caps.append(Capability(
        id="sounddevice",
        ok=module_available("sounddevice"),
        required_for="native microphone capture fallback",
        detail="Native audio capture package",
        install_hint="pip install -e .[local-ai]",
    ))
    codex_logged_in, codex_detail = codex_login_status()
    caps.append(Capability(
        id="codex-cli",
        ok=shutil.which("codex") is not None,
        required_for="OpenAI Codex account-backed LLM provider",
        detail=shutil.which("codex") or "codex CLI not found",
        install_hint="Install official OpenAI Codex CLI if this provider is enabled.",
    ))
    caps.append(Capability(
        id="codex-login",
        ok=codex_logged_in,
        required_for="OpenAI Codex account-backed LLM provider",
        detail=codex_detail,
        install_hint="Run official Codex login with ChatGPT/Codex account; do not use API key for this product path.",
    ))
    return caps


def required_runtime_ok() -> bool:
    required_ids = {"ffmpeg-bundled", "keyring", "faster-whisper", "whisper-model-small"}
    return all(c.ok for c in check_capabilities() if c.id in required_ids)
