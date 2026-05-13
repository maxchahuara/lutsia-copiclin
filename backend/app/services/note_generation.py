from typing import Protocol
from app.schemas.clinical_note import ClinicalNoteResult, TrazabilidadItem


class LLMProvider(Protocol):
    def generate_structured_note(self, transcript: dict, **kwargs: object) -> ClinicalNoteResult: ...


class MockLLMProvider:
    provider_id = "mock"

    def generate_structured_note(self, transcript: dict, **_: object) -> ClinicalNoteResult:
        text = " ".join(segment.get("text", "") for segment in transcript.get("segments", []))
        note = ClinicalNoteResult()
        note.metadata.quality_warnings = [] if text else ["No se detectó información suficiente"]
        note.metadata.missing_information = [
            "Examen físico",
            "Antecedentes quirúrgicos",
            "Medicamentos habituales",
        ]
        if "tos" in text.lower():
            note.resumen_breve = "Paciente refiere tos desde hace tres días; niega fiebre."
            note.motivo_consulta = "Tos"
            note.anamnesis.enfermedad_actual = "Tos desde hace tres días. Niega fiebre."
            note.anamnesis.alergias = "No tiene alergias conocidas, según transcripción."
            note.bloques_copiables.resumen_para_medico = note.resumen_breve
            note.bloques_copiables.anamnesis_compacta = note.anamnesis.enfermedad_actual
            note.bloques_copiables.soap.subjetivo = note.anamnesis.enfermedad_actual
            note.trazabilidad.append(
                TrazabilidadItem(seccion="anamnesis.enfermedad_actual", segment_ids=["seg-002"], comentario="Dato explícito en transcripción")
            )
        else:
            note.resumen_breve = "No mencionado"
        return note
