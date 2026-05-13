from __future__ import annotations

from app.services.codex_account import CodexAccountProvider
from app.services.runtime_checks import check_capabilities
from app.services.whisper_models import is_model_installed, list_model_statuses


def first_run_setup_status(settings) -> dict[str, object]:
    capabilities = {cap.id: cap for cap in check_capabilities()}
    codex_status = CodexAccountProvider().status()
    selected_model_ready = is_model_installed(settings.transcription_model_name)

    required_steps = [
        {
            "id": "codex-account",
            "title": "Iniciar sesion con ChatGPT",
            "ok": codex_status.logged_in,
            "required": True,
            "detail": "Cuenta conectada"
            if codex_status.logged_in
            else "Pendiente de inicio de sesion",
        },
        {
            "id": "whisper-local",
            "title": "Transcripcion local",
            "ok": bool(capabilities.get("faster-whisper") and capabilities["faster-whisper"].ok),
            "required": True,
            "detail": "Whisper esta instalado localmente",
        },
        {
            "id": "whisper-model",
            "title": "Modelo Whisper seleccionado",
            "ok": selected_model_ready,
            "required": True,
            "detail": f"Modelo activo: {settings.transcription_model_name}",
        },
        {
            "id": "audio-runtime",
            "title": "Audio local",
            "ok": bool(capabilities.get("ffmpeg-bundled") and capabilities["ffmpeg-bundled"].ok),
            "required": True,
            "detail": "Conversion de audio lista",
        },
    ]
    optional_steps = [
        {
            "id": "microphone-runtime",
            "title": "Microfono local",
            "ok": bool(capabilities.get("sounddevice") and capabilities["sounddevice"].ok),
            "required": False,
            "detail": "Captura nativa disponible"
            if capabilities.get("sounddevice") and capabilities["sounddevice"].ok
            else "Captura nativa pendiente",
        },
        {
            "id": "safe-use",
            "title": "Confirmar uso seguro",
            "ok": bool(settings.setup_completed),
            "required": False,
            "detail": "El medico revisa cada borrador antes de usarlo.",
        },
    ]
    all_required_ok = all(bool(step["ok"]) for step in required_steps)
    return {
        "setup_completed": bool(settings.setup_completed),
        "ready_for_real_use": all_required_ok and bool(settings.setup_completed),
        "can_run_demo": False,
        "required_steps": required_steps,
        "optional_steps": optional_steps,
        "warnings": [],
        "codex": codex_status.to_dict(),
        "whisper_models": list_model_statuses(settings.transcription_model_name),
    }
