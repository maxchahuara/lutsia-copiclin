from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from app.paths import app_data_dir
from app.schemas.clinical_note import ClinicalNoteResult
from app.schemas.core import ConsultationCreate, ConsultationRead, PatientCreate, PatientRead, SettingsRead, utcnow


class MemoryStore:
    """Small local JSON store for the first desktop prototype.

    It is intentionally simple and per-user. Future versions can migrate this to
    SQLCipher/SQLite without changing the API surface.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or app_data_dir() / "store.json"
        self.settings = SettingsRead()
        self.patients: dict[str, PatientRead] = {}
        self.consultations: dict[str, ConsultationRead] = {}
        self.transcripts: dict[str, dict] = {}
        self.notes: dict[str, ClinicalNoteResult] = {}
        self.audio_files: dict[str, list[dict[str, object]]] = {}
        self.load()

    def load(self) -> None:
        if not self.db_path.exists():
            return
        try:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # Fail closed to a blank in-memory store rather than crashing the app.
            return
        self.settings = SettingsRead.model_validate(data.get("settings") or {})
        self.patients = {
            pid: PatientRead.model_validate(value)
            for pid, value in (data.get("patients") or {}).items()
        }
        self.consultations = {
            cid: ConsultationRead.model_validate(value)
            for cid, value in (data.get("consultations") or {}).items()
        }
        self.transcripts = data.get("transcripts") or {}
        self.notes = {
            cid: ClinicalNoteResult.model_validate(value)
            for cid, value in (data.get("notes") or {}).items()
        }
        self.audio_files = data.get("audio_files") or {}

    def save(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "settings": self.settings.model_dump(mode="json"),
            "patients": {pid: item.model_dump(mode="json") for pid, item in self.patients.items()},
            "consultations": {
                cid: item.model_dump(mode="json") for cid, item in self.consultations.items()
            },
            "transcripts": self.transcripts,
            "notes": {cid: note.model_dump(mode="json") for cid, note in self.notes.items()},
            "audio_files": self.audio_files,
        }
        tmp = self.db_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.db_path)

    def create_consultation(self, payload: ConsultationCreate) -> ConsultationRead:
        consultation = ConsultationRead(id=str(uuid4()), **payload.model_dump())
        self.consultations[consultation.id] = consultation
        self.save()
        return consultation

    def create_patient(self, payload: PatientCreate) -> PatientRead:
        patient = PatientRead(id=str(uuid4()), **payload.model_dump())
        self.patients[patient.id] = patient
        self.save()
        return patient

    def update_patient_timestamp(self, patient_id: str) -> None:
        if patient_id in self.patients:
            self.patients[patient_id].updated_at = utcnow()


store = MemoryStore()
