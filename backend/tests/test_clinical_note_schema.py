from app.schemas.clinical_note import ClinicalNoteResult
from app.services.note_generation import MockLLMProvider


def test_empty_note_defaults_to_no_mencionado():
    note = ClinicalNoteResult()
    assert note.resumen_breve == "No mencionado"
    assert note.anamnesis.alergias == "No mencionado"


def test_mock_note_handles_negation_and_traceability():
    transcript = {"segments": [{"id": "seg-002", "text": "Tengo tos desde hace tres días y niego fiebre. No tengo alergias conocidas."}]}
    note = MockLLMProvider().generate_structured_note(transcript)
    assert "tos" in note.resumen_breve.lower()
    assert "niega fiebre" in note.anamnesis.enfermedad_actual.lower()
    assert note.trazabilidad[0].segment_ids == ["seg-002"]
