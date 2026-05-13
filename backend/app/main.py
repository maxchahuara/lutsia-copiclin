from fastapi import FastAPI, HTTPException

from app.schemas.clinical_note import ClinicalNoteResult
from app.schemas.core import ConsultationCreate, ConsultationRead, SettingsRead, SettingsUpdate
from app.services.memory_store import store
from app.services.note_generation import MockLLMProvider
from app.services.transcription import MockTranscriptionProvider

app = FastAPI(title="LUTSIA CopiClin Local API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "LUTSIA CopiClin"}


@app.get("/settings", response_model=SettingsRead)
def get_settings() -> SettingsRead:
    return store.settings


@app.put("/settings", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate) -> SettingsRead:
    store.settings = store.settings.model_copy(update=payload.model_dump(exclude_unset=True))
    return store.settings


@app.post("/consultations", response_model=ConsultationRead)
def create_consultation(payload: ConsultationCreate) -> ConsultationRead:
    return store.create_consultation(payload)


@app.get("/consultations", response_model=list[ConsultationRead])
def list_consultations() -> list[ConsultationRead]:
    return list(store.consultations.values())


@app.get("/consultations/{consultation_id}", response_model=ConsultationRead)
def get_consultation(consultation_id: str) -> ConsultationRead:
    try:
        return store.consultations[consultation_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Consultation not found") from exc


@app.get("/providers")
def providers() -> dict[str, list[dict[str, str | bool]]]:
    return {
        "transcription": [
            {"id": "mock", "name": "Mock transcription", "local": True, "enabled": True},
            {"id": "faster-whisper", "name": "Local faster-whisper", "local": True, "enabled": False},
            {"id": "whisper-cpp", "name": "Local whisper.cpp", "local": True, "enabled": False},
        ],
        "llm": [
            {"id": "mock", "name": "Mock clinical note generator", "local": True, "enabled": True},
            {"id": "ollama", "name": "Local Ollama", "local": True, "enabled": False},
            {"id": "codex-account", "name": "Experimental Codex account bridge", "local": False, "enabled": False},
        ],
    }


@app.post("/consultations/{consultation_id}/transcribe")
def transcribe(consultation_id: str):
    if consultation_id not in store.consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")
    result = MockTranscriptionProvider().transcribe(consultation_id=consultation_id)
    store.transcripts[consultation_id] = result
    return result


@app.get("/consultations/{consultation_id}/transcript")
def get_transcript(consultation_id: str):
    return store.transcripts.get(consultation_id, {"segments": []})


@app.post("/consultations/{consultation_id}/generate-note", response_model=ClinicalNoteResult)
def generate_note(consultation_id: str) -> ClinicalNoteResult:
    if consultation_id not in store.consultations:
        raise HTTPException(status_code=404, detail="Consultation not found")
    transcript = store.transcripts.get(consultation_id, {"segments": []})
    note = MockLLMProvider().generate_structured_note(transcript=transcript)
    store.notes[consultation_id] = note
    return note


@app.get("/consultations/{consultation_id}/note", response_model=ClinicalNoteResult | None)
def get_note(consultation_id: str):
    return store.notes.get(consultation_id)
