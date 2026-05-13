from datetime import datetime, timezone
from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConsultationCreate(BaseModel):
    title: str = "Nueva consulta"
    specialty: str = "medicina_general"
    language: str = "es"
    consent_confirmed: bool = False
    patient_label: str | None = None


class ConsultationRead(ConsultationCreate):
    id: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    status: str = "created"
    local_storage_path: str | None = None


class SettingsRead(BaseModel):
    language: str = "es"
    transcription_provider: str = "mock"
    llm_provider: str = "codex-account"
    model_name: str = "codex-account-default"
    encryption_enabled: bool = True
    telemetry_enabled: bool = False
    data_retention_policy: str = "keep_until_deleted"
    ai_account_mode: str = "codex_account_login"
    setup_completed: bool = False
    setup_mode: str = "required"


class SettingsUpdate(BaseModel):
    language: str | None = None
    transcription_provider: str | None = None
    llm_provider: str | None = None
    model_name: str | None = None
    encryption_enabled: bool | None = None
    telemetry_enabled: bool | None = None
    data_retention_policy: str | None = None
    setup_completed: bool | None = None
    setup_mode: str | None = None
