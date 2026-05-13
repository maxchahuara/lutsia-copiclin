from fastapi.testclient import TestClient
from app.main import app
from app.services.codex_account import CODEX_CONFIG, parse_device_auth_output


def test_codex_auth_endpoints_are_per_user_app_scoped():
    client = TestClient(app)
    status = client.get("/auth/codex/status").json()
    assert status["auth_scope"] in {"per-user app CODEX_HOME", "existing per-user Codex session"}
    assert "CopiClin" in status["codex_home"]

    instructions = client.get("/auth/codex/login-instructions").json()
    assert instructions["method"] == "official-codex-device-auth"
    assert instructions["command"] == "codex login --device-auth"
    assert instructions["environment"]["CODEX_HOME"] == status["codex_home"]


def test_codex_device_auth_output_parser_extracts_url_and_code():
    text = """
    Open this link in your browser:
    https://auth.openai.com/codex/device
    Enter this one-time code:
    ZU28-MXNGQ
    """
    auth_url, user_code = parse_device_auth_output(text)
    assert auth_url == "https://auth.openai.com/codex/device"
    assert user_code == "ZU28-MXNGQ"


def test_app_codex_config_uses_file_store_for_windows_token_size_limit():
    assert 'cli_auth_credentials_store = "file"' in CODEX_CONFIG
