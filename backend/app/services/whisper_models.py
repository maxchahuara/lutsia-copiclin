from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from app.paths import whisper_models_dir


@dataclass(frozen=True)
class WhisperModelOption:
    id: str
    name: str
    speed: str
    quality: str
    size: str
    recommended_for: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


WHISPER_MODELS = [
    WhisperModelOption(
        "tiny",
        "Tiny",
        "muy rapida",
        "basica",
        "muy liviano",
        "equipos modestos y borradores rapidos",
    ),
    WhisperModelOption(
        "base", "Base", "rapida", "aceptable", "liviano", "consultas cortas con buen audio"
    ),
    WhisperModelOption("small", "Small", "equilibrada", "buena", "medio", "uso diario recomendado"),
    WhisperModelOption(
        "medium", "Medium", "media", "muy buena", "alto", "mayor precision si el equipo lo soporta"
    ),
    WhisperModelOption(
        "large-v3", "Large v3", "lenta", "maxima", "muy alto", "maxima calidad en equipos potentes"
    ),
    WhisperModelOption(
        "turbo", "Turbo", "rapida", "alta", "alto", "buen balance en equipos modernos"
    ),
]


def valid_model_ids() -> set[str]:
    return {model.id for model in WHISPER_MODELS}


def _model_root(model_id: str) -> Path:
    return whisper_models_dir() / model_id


def is_model_installed(model_id: str) -> bool:
    root = _model_root(model_id)
    if not root.exists():
        return False
    for model_bin in root.rglob("model.bin"):
        try:
            if model_bin.exists() and model_bin.stat().st_size > 0:
                return True
        except OSError:
            continue
    return False


def model_status(model_id: str, selected_model: str | None = None) -> dict[str, object]:
    option = next(model for model in WHISPER_MODELS if model.id == model_id)
    root = _model_root(model_id)
    return {
        **option.to_dict(),
        "installed": is_model_installed(model_id),
        "selected": model_id == selected_model,
        "local_path": str(root),
    }


def list_model_statuses(selected_model: str) -> list[dict[str, object]]:
    return [model_status(model.id, selected_model) for model in WHISPER_MODELS]


def download_whisper_model(model_id: str) -> dict[str, object]:
    if model_id not in valid_model_ids():
        raise ValueError(f"Unsupported Whisper model: {model_id}")

    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
    try:
        from huggingface_hub import constants as hf_constants  # type: ignore

        hf_constants.HF_HUB_DISABLE_XET = True
        hf_constants.HF_HUB_DISABLE_SYMLINKS = True
    except Exception:
        pass

    root = _model_root(model_id)
    if root.exists() and not is_model_installed(model_id):
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on install
        raise RuntimeError("faster-whisper is not installed") from exc

    WhisperModel(model_id, device="cpu", compute_type="int8", download_root=str(root))
    return model_status(model_id, model_id)
