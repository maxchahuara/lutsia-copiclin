from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass, asdict


@dataclass
class Capability:
    id: str
    ok: bool
    required_for: str
    detail: str
    install_hint: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


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
    caps.append(Capability(
        id="faster-whisper",
        ok=module_available("faster_whisper"),
        required_for="local Whisper transcription",
        detail="Local Whisper backend package",
        install_hint="pip install -e .[local-ai]",
    ))
    caps.append(Capability(
        id="sounddevice",
        ok=module_available("sounddevice"),
        required_for="native microphone capture fallback",
        detail="Native audio capture package",
        install_hint="pip install -e .[local-ai]",
    ))
    caps.append(Capability(
        id="ollama",
        ok=shutil.which("ollama") is not None,
        required_for="local LLM provider",
        detail=shutil.which("ollama") or "ollama CLI not found",
        install_hint="Install Ollama from official packages if using local LLMs.",
    ))
    caps.append(Capability(
        id="codex-cli",
        ok=shutil.which("codex") is not None,
        required_for="experimental account-backed provider",
        detail=shutil.which("codex") or "codex CLI not found",
        install_hint="Install official OpenAI Codex CLI if this provider is enabled.",
    ))
    return caps


def required_runtime_ok() -> bool:
    required_ids = {"ffmpeg-bundled", "keyring"}
    return all(c.ok for c in check_capabilities() if c.id in required_ids)
