from uuid import uuid4
from app.schemas.core import ConsultationCreate, ConsultationRead, SettingsRead


class MemoryStore:
    def __init__(self) -> None:
        self.settings = SettingsRead()
        self.consultations: dict[str, ConsultationRead] = {}
        self.transcripts: dict[str, dict] = {}
        self.notes: dict[str, object] = {}
        self.audio_files: dict[str, list[dict[str, object]]] = {}

    def create_consultation(self, payload: ConsultationCreate) -> ConsultationRead:
        consultation = ConsultationRead(id=str(uuid4()), **payload.model_dump())
        self.consultations[consultation.id] = consultation
        return consultation


store = MemoryStore()
