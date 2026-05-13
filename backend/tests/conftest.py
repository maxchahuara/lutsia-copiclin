from __future__ import annotations

import pytest

from app.schemas.core import SettingsRead
from app.services.memory_store import store


@pytest.fixture(autouse=True)
def reset_store_for_test(tmp_path):
    store.db_path = tmp_path / "store.json"
    store.settings = SettingsRead(llm_provider="mock", transcription_provider="mock")
    store.consultations.clear()
    store.transcripts.clear()
    store.notes.clear()
    store.audio_files.clear()
    yield
    store.consultations.clear()
    store.transcripts.clear()
    store.notes.clear()
    store.audio_files.clear()
