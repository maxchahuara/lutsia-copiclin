from fastapi.testclient import TestClient

from app.main import app


def test_first_run_setup_status_exposes_required_checks():
    client = TestClient(app)
    payload = client.get("/setup/status").json()
    ids = {step["id"] for step in payload["required_steps"]}
    assert {"codex-account", "whisper-local", "whisper-model", "audio-runtime"}.issubset(ids)
    assert all("action" not in step for step in payload["required_steps"])
    assert "codex" in payload
    assert "whisper_models" in payload
    assert payload["can_run_demo"] is False
    assert payload["ready_for_real_use"] is False


def test_setup_complete_marks_review_but_does_not_fake_runtime_readiness():
    client = TestClient(app)
    response = client.post("/setup/complete")
    assert response.status_code == 200
    assert response.json()["setup_completed"] is True
    payload = client.get("/setup/status").json()
    assert payload["setup_completed"] is True
    assert "required_steps" in payload


def test_transcription_models_are_product_options():
    client = TestClient(app)
    payload = client.get("/transcription/models").json()
    model_ids = {model["id"] for model in payload["models"]}
    assert {"tiny", "base", "small", "medium", "large-v3", "turbo"}.issubset(model_ids)
    assert payload["selected"] == "small"


def test_transcription_model_selection_validates_supported_models():
    client = TestClient(app)
    response = client.put("/transcription/model", json={"model_name": "tiny"})
    assert response.status_code == 200
    assert response.json()["transcription_model_name"] == "tiny"

    response = client.put("/transcription/model", json={"model_name": "unknown"})
    assert response.status_code == 400
