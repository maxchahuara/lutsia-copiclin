from __future__ import annotations

from app.services.codex_account import CodexAccountProvider
from app.services.runtime_checks import check_capabilities


def first_run_setup_status(settings) -> dict[str, object]:
    capabilities = {cap.id: cap for cap in check_capabilities()}
    codex = CodexAccountProvider()
    codex_status = codex.status()

    required_steps = [
        {
            "id": "codex-account",
            "title": "Conectar cuenta ChatGPT/Codex",
            "ok": codex_status.logged_in,
            "required": True,
            "detail": codex_status.detail,
            "action": codex.login_instructions(),
        },
        {
            "id": "whisper-local",
            "title": "Verificar transcripción local Whisper/faster-whisper",
            "ok": bool(capabilities.get("faster-whisper") and capabilities["faster-whisper"].ok),
            "required": True,
            "detail": capabilities.get("faster-whisper").detail if capabilities.get("faster-whisper") else "not checked",
            "action": {
                "command": "pip install -e '.[local-ai]'",
                "notes": [
                    "Instala faster-whisper y dependencias locales de audio.",
                    "Los modelos grandes no se descargan automáticamente; el usuario debe elegir tamaño/modelo.",
                ],
            },
        },
        {
            "id": "audio-runtime",
            "title": "Verificar runtime de audio/FFmpeg",
            "ok": bool(capabilities.get("ffmpeg-bundled") and capabilities["ffmpeg-bundled"].ok),
            "required": True,
            "detail": capabilities.get("ffmpeg-bundled").detail if capabilities.get("ffmpeg-bundled") else "not checked",
            "action": {"command": "pip install imageio-ffmpeg"},
        },
    ]
    optional_steps = [
        {
            "id": "microphone-runtime",
            "title": "Micrófono local",
            "ok": bool(capabilities.get("sounddevice") and capabilities["sounddevice"].ok),
            "required": False,
            "detail": capabilities.get("sounddevice").detail if capabilities.get("sounddevice") else "not checked",
            "action": {"command": "pip install -e '.[local-ai]'"},
        },
        {
            "id": "safe-use",
            "title": "Confirmar uso seguro",
            "ok": bool(settings.setup_completed),
            "required": False,
            "detail": "CopiClin genera borradores: el médico debe revisar antes de copiar/usar.",
            "action": {"button": "Marcar configuración revisada"},
        },
    ]
    all_required_ok = all(bool(step["ok"]) for step in required_steps)
    return {
        "setup_completed": bool(settings.setup_completed),
        "ready_for_real_use": all_required_ok and bool(settings.setup_completed),
        "can_run_demo": True,
        "required_steps": required_steps,
        "optional_steps": optional_steps,
        "warnings": [
            "No uses CopiClin con pacientes reales hasta conectar Codex y verificar transcripción local.",
            "El proveedor Codex real todavía falla cerrado hasta validar la integración no-interactiva oficial.",
        ],
    }
