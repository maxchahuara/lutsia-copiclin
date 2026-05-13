from fastapi.testclient import TestClient
from app.main import app


def test_codex_auth_endpoints_are_per_user_app_scoped():
    client = TestClient(app)
    status = client.get("/auth/codex/status").json()
    assert status["auth_scope"] == "per-user app CODEX_HOME"
    assert "CopiClin" in status["codex_home"]

    instructions = client.get("/auth/codex/login-instructions").json()
    assert instructions["method"] == "official-codex-device-auth"
    assert instructions["command"] == "codex login --device-auth"
    assert instructions["environment"]["CODEX_HOME"] == status["codex_home"]
