from pydantic import BaseModel, Field

NO_MENCIONADO = "No mencionado"


class Metadata(BaseModel):
    language: str = "es"
    specialty: str = "medicina_general"
    source: str = "transcript"
    quality_warnings: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class Anamnesis(BaseModel):
    enfermedad_actual: str = NO_MENCIONADO
    antecedentes_personales: str = NO_MENCIONADO
    antecedentes_quirurgicos: str = NO_MENCIONADO
    antecedentes_familiares: str = NO_MENCIONADO
    medicamentos_habituales: str = NO_MENCIONADO
    alergias: str = NO_MENCIONADO
    habitos: str = NO_MENCIONADO
    revision_por_sistemas: str = NO_MENCIONADO


class PlanMencionado(BaseModel):
    medicacion: list[str] = Field(default_factory=list)
    examenes: list[str] = Field(default_factory=list)
    referencias: list[str] = Field(default_factory=list)
    educacion: list[str] = Field(default_factory=list)
    seguimiento: str = NO_MENCIONADO


class SOAP(BaseModel):
    subjetivo: str = NO_MENCIONADO
    objetivo: str = NO_MENCIONADO
    analisis: str = NO_MENCIONADO
    plan: str = NO_MENCIONADO


class BloquesCopiables(BaseModel):
    soap: SOAP = Field(default_factory=SOAP)
    historia_clinica_narrativa: str = NO_MENCIONADO
    anamnesis_compacta: str = NO_MENCIONADO
    indicaciones: str = NO_MENCIONADO
    resumen_para_medico: str = NO_MENCIONADO


class TrazabilidadItem(BaseModel):
    seccion: str
    segment_ids: list[str] = Field(default_factory=list)
    comentario: str = ""


class ClinicalNoteResult(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    resumen_breve: str = NO_MENCIONADO
    motivo_consulta: str = NO_MENCIONADO
    anamnesis: Anamnesis = Field(default_factory=Anamnesis)
    examen_fisico_mencionado: str = NO_MENCIONADO
    resultados_mencionados: str = NO_MENCIONADO
    impresion_o_diagnosticos_mencionados: list[str] = Field(default_factory=list)
    plan_mencionado: PlanMencionado = Field(default_factory=PlanMencionado)
    signos_alarma_mencionados: list[str] = Field(default_factory=list)
    pendientes: list[str] = Field(default_factory=list)
    incertidumbres: list[str] = Field(default_factory=list)
    bloques_copiables: BloquesCopiables = Field(default_factory=BloquesCopiables)
    trazabilidad: list[TrazabilidadItem] = Field(default_factory=list)
    edited_by_user: bool = False
    verified_sections: list[str] = Field(default_factory=list)
