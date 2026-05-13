from fastapi.testclient import TestClient
from app.main import app
from app.services.codex_account import CodexAccountStatus, CodexAccountProvider


def test_vertical_api_flow_generates_copyable_note():
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    created = client.post("/consultations", json={"title": "Consulta prueba", "consent_confirmed": True}).json()
    cid = created["id"]
    transcript = client.post(f"/consultations/{cid}/transcribe").json()
    assert transcript["segments"]
    note = client.post(f"/consultations/{cid}/generate-note").json()
    assert "tos" in note["resumen_breve"].lower()
    assert note["bloques_copiables"]["resumen_para_medico"]
    assert note["trazabilidad"]


def test_audio_upload_endpoint_accepts_file():
    client = TestClient(app)
    cid = client.post("/consultations", json={"title": "Con audio", "consent_confirmed": True}).json()["id"]
    response = client.post(
        f"/consultations/{cid}/audio/upload",
        files={"file": ("sample.webm", b"fake-audio-bytes", "audio/webm")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["size_bytes"] == len(b"fake-audio-bytes")


def test_requires_consent_before_audio_processing():
    client = TestClient(app)
    cid = client.post("/consultations", json={"title": "Sin consentimiento"}).json()["id"]
    response = client.post(f"/consultations/{cid}/transcribe")
    assert response.status_code == 409


def test_patient_creation_and_consultation_listing_uses_real_patients():
    client = TestClient(app)
    legacy = client.post(
        "/consultations",
        json={"title": "Consulta de prueba", "consent_confirmed": True},
    ).json()
    patient = client.post(
        "/patients",
        json={"full_name": "Paciente Real", "identifier": "HC-001"},
    ).json()
    real = client.post(
        "/consultations",
        json={
            "title": "Entrevista real",
            "consent_confirmed": True,
            "patient_id": patient["id"],
            "patient_label": patient["full_name"],
        },
    ).json()

    patients = client.get("/patients").json()
    consultations = client.get("/consultations").json()

    assert [item["full_name"] for item in patients] == ["Paciente Real"]
    assert [item["id"] for item in consultations] == [real["id"]]
    assert legacy["id"] not in [item["id"] for item in consultations]


def test_codex_provider_fails_closed_without_user_login(monkeypatch):
    monkeypatch.setattr(
        CodexAccountProvider,
        "status",
        lambda self: CodexAccountStatus(True, False, "not logged in", "test-codex-home"),
    )
    client = TestClient(app)
    client.put("/settings", json={"llm_provider": "codex-account"})
    cid = client.post("/consultations", json={"title": "Codex", "consent_confirmed": True}).json()["id"]
    client.post(f"/consultations/{cid}/transcribe")
    response = client.post(f"/consultations/{cid}/generate-note")
    assert response.status_code == 409
