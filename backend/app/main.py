from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.schemas.clinical_note import ClinicalNoteResult
from app.schemas.core import ConsultationCreate, ConsultationRead, SettingsRead, SettingsUpdate, utcnow
from app.services.audio_storage import save_upload
from app.services.codex_account import CodexAccountProvider
from app.services.memory_store import store
from app.services.runtime_checks import check_capabilities, codex_login_status
from app.services.setup_status import first_run_setup_status
from app.services.note_generation import MockLLMProvider
from app.services.transcription import LocalFasterWhisperProvider, MockTranscriptionProvider

app = FastAPI(title="LUTSIA CopiClin Local API", version="0.1.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


def _require_consultation(consultation_id: str):
    try:
        consultation = store.consultations[consultation_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Consultation not found") from exc
    return consultation


def _require_consent(consultation_id: str):
    consultation = _require_consultation(consultation_id)
    if not consultation.consent_confirmed:
        raise HTTPException(status_code=409, detail="Consent must be confirmed before audio processing")
    return consultation


@app.get("/", include_in_schema=False)
def root():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "LUTSIA CopiClin"}


@app.get("/settings", response_model=SettingsRead)
def get_settings() -> SettingsRead:
    return store.settings


@app.put("/settings", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate) -> SettingsRead:
    store.settings = store.settings.model_copy(update=payload.model_dump(exclude_unset=True))
    store.save()
    return store.settings


@app.post("/consultations", response_model=ConsultationRead)
def create_consultation(payload: ConsultationCreate) -> ConsultationRead:
    return store.create_consultation(payload)


@app.get("/consultations", response_model=list[ConsultationRead])
def list_consultations() -> list[ConsultationRead]:
    return list(store.consultations.values())


@app.get("/consultations/{consultation_id}", response_model=ConsultationRead)
def get_consultation(consultation_id: str) -> ConsultationRead:
    return _require_consultation(consultation_id)


@app.get("/runtime/capabilities")
def runtime_capabilities():
    return {"capabilities": [cap.to_dict() for cap in check_capabilities()]}


@app.get("/setup/status")
def setup_status():
    return first_run_setup_status(store.settings)


@app.post("/setup/complete", response_model=SettingsRead)
def complete_setup():
    store.settings = store.settings.model_copy(update={"setup_completed": True})
    store.save()
    return store.settings


@app.post("/setup/reset", response_model=SettingsRead)
def reset_setup():
    store.settings = store.settings.model_copy(update={"setup_completed": False})
    store.save()
    return store.settings


@app.get("/auth/codex/status")
def codex_auth_status():
    return CodexAccountProvider().status().to_dict()


@app.get("/auth/codex/login-instructions")
def codex_login_instructions():
    return CodexAccountProvider().login_instructions()


@app.get("/providers")
def providers() -> dict[str, list[dict[str, str | bool]]]:
    return {
        "transcription": [
            {"id": "mock", "name": "Mock transcription", "local": True, "enabled": True},
            {"id": "faster-whisper", "name": "Local faster-whisper", "local": True, "enabled": False},
            {"id": "whisper-cpp", "name": "Local whisper.cpp", "local": True, "enabled": False},
        ],
        "llm": [
            {"id": "codex-account", "name": "OpenAI Codex account login", "local": False, "enabled": codex_login_status()[0]},
            {"id": "mock", "name": "Mock clinical note generator (dev/test only)", "local": True, "enabled": False, "dev_only": True},
        ],
    }


@app.post("/consultations/{consultation_id}/audio/upload")
async def upload_audio(consultation_id: str, file: UploadFile = File(...)):
    _require_consent(consultation_id)
    audio = await save_upload(consultation_id, file)
    store.audio_files.setdefault(consultation_id, []).append(audio)
    store.consultations[consultation_id].updated_at = utcnow()
    store.save()
    return audio


@app.post("/consultations/{consultation_id}/transcribe")
def transcribe(consultation_id: str):
    _require_consent(consultation_id)
    latest_audio = (store.audio_files.get(consultation_id) or [{}])[-1].get("path")
    if store.settings.transcription_provider == "faster-whisper":
        if not latest_audio:
            raise HTTPException(status_code=409, detail="Upload audio before local transcription")
        result = LocalFasterWhisperProvider(model_name=store.settings.transcription_model_name).transcribe(audio_path=str(latest_audio), language=store.settings.language)
    else:
        result = MockTranscriptionProvider().transcribe(consultation_id=consultation_id, audio_path=latest_audio)
    store.transcripts[consultation_id] = result
    store.consultations[consultation_id].updated_at = utcnow()
    store.save()
    return result


@app.get("/consultations/{consultation_id}/transcript")
def get_transcript(consultation_id: str):
    return store.transcripts.get(consultation_id, {"segments": []})


@app.post("/consultations/{consultation_id}/generate-note", response_model=ClinicalNoteResult)
def generate_note(consultation_id: str) -> ClinicalNoteResult:
    _require_consent(consultation_id)
    transcript = store.transcripts.get(consultation_id, {"segments": []})
    if store.settings.llm_provider == "codex-account":
        status = CodexAccountProvider().status()
        if not status.logged_in:
            raise HTTPException(status_code=409, detail={"message": "Codex account is not logged in for this app user", "status": status.to_dict(), "login": CodexAccountProvider().login_instructions()})
        try:
            note = CodexAccountProvider().generate_structured_note(transcript=transcript)
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
    elif store.settings.llm_provider == "mock":
        note = MockLLMProvider().generate_structured_note(transcript=transcript)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported LLM provider: {store.settings.llm_provider}")
    store.notes[consultation_id] = note
    store.consultations[consultation_id].updated_at = utcnow()
    store.save()
    return note


@app.get("/consultations/{consultation_id}/note", response_model=ClinicalNoteResult | None)
def get_note(consultation_id: str):
    return store.notes.get(consultation_id)


def run_dev() -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=8765, reload=False)
