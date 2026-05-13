from fastapi.testclient import TestClient
from app.main import app


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
