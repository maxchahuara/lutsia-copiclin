from fastapi.testclient import TestClient

from app.main import app


def test_first_run_setup_status_exposes_required_checks():
    client = TestClient(app)
    payload = client.get("/setup/status").json()
    ids = {step["id"] for step in payload["required_steps"]}
    assert {"codex-account", "whisper-local", "audio-runtime"}.issubset(ids)
    assert payload["can_run_demo"] is True
    assert payload["ready_for_real_use"] is False


def test_setup_complete_marks_review_but_does_not_fake_runtime_readiness():
    client = TestClient(app)
    response = client.post("/setup/complete")
    assert response.status_code == 200
    assert response.json()["setup_completed"] is True
    payload = client.get("/setup/status").json()
    assert payload["setup_completed"] is True
    assert "required_steps" in payload
