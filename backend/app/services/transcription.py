from __future__ import annotations

from typing import Protocol, Callable, Any

from app.paths import whisper_models_dir


class TranscriptionProvider(Protocol):
    def transcribe(
        self,
        audio_path: str | None = None,
        language: str = "es",
        diarization: bool = False,
        glossary: list[str] | None = None,
        progress_callback: Callable[[float], Any] | None = None,
    ) -> dict: ...


class MockTranscriptionProvider:
    provider_id = "mock"

    def transcribe(self, consultation_id: str | None = None, audio_path: str | None = None, **_: object) -> dict:
        return {
            "consultation_id": consultation_id,
            "audio_path": audio_path,
            "language": "es",
            "provider": self.provider_id,
            "quality_warnings": [],
            "segments": [
                {
                    "id": "seg-001",
                    "speaker_label": "medico",
                    "start_time": 0.0,
                    "end_time": 4.0,
                    "text": "¿Cuál es el motivo de consulta de hoy?",
                    "confidence": 0.99,
                    "source_provider": self.provider_id,
                },
                {
                    "id": "seg-002",
                    "speaker_label": "paciente",
                    "start_time": 4.0,
                    "end_time": 12.0,
                    "text": "Tengo tos desde hace tres días y niego fiebre. No tengo alergias conocidas.",
                    "confidence": 0.98,
                    "source_provider": self.provider_id,
                },
            ],
        }


class LocalFasterWhisperProvider:
    provider_id = "faster-whisper"

    def __init__(self, model_name: str = "small", device: str = "cpu") -> None:
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on optional install
            raise RuntimeError("faster-whisper is not installed. Install with: pip install -e .[local-ai]") from exc
        model_dir = whisper_models_dir() / model_name
        self._model = WhisperModel(model_name, device=device, compute_type="int8", download_root=str(model_dir))

    def transcribe(self, audio_path: str | None = None, language: str = "es", **_: object) -> dict:
        if not audio_path:
            raise ValueError("audio_path is required for faster-whisper transcription")
        segments, info = self._model.transcribe(audio_path, language=language)
        result_segments = []
        for index, seg in enumerate(segments, start=1):
            result_segments.append({
                "id": f"fw-{index:04d}",
                "speaker_label": "desconocido",
                "start_time": float(seg.start),
                "end_time": float(seg.end),
                "text": seg.text.strip(),
                "confidence": None,
                "source_provider": self.provider_id,
            })
        return {
            "audio_path": audio_path,
            "language": getattr(info, "language", language),
            "provider": self.provider_id,
            "quality_warnings": [],
            "segments": result_segments,
        }
