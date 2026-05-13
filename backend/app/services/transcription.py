from typing import Protocol, Callable, Any


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

    def transcribe(self, consultation_id: str | None = None, **_: object) -> dict:
        return {
            "consultation_id": consultation_id,
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
