from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from shutil import which

APP_DATA_HOME = Path.home() / ".local" / "share" / "lutsia-copiclin"
APP_CODEX_HOME = APP_DATA_HOME / "codex"


@dataclass
class CodexAccountStatus:
    available: bool
    logged_in: bool
    detail: str
    codex_home: str
    auth_scope: str = "per-user app CODEX_HOME"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def codex_env() -> dict[str, str]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(APP_CODEX_HOME)
    return env


def ensure_codex_home() -> None:
    APP_CODEX_HOME.mkdir(parents=True, exist_ok=True)
    config = APP_CODEX_HOME / "config.toml"
    if not config.exists():
        config.write_text(
            '# LUTSIA CopiClin app-specific Codex config\n'
            '# Store credentials in OS keychain when supported; never in the project repo.\n'
            'cli_auth_credentials_store = "keyring"\n'
            'forced_login_method = "chatgpt"\n'
        )


class CodexAccountProvider:
    """Per-user account-backed provider using official Codex CLI only.

    Each installed user signs in with their own ChatGPT/Codex account. The app
    uses an app-specific CODEX_HOME so it does not read, modify, or depend on a
    developer/operator ~/.codex directory.
    """

    provider_id = "codex-account"

    def status(self) -> CodexAccountStatus:
        codex = which("codex")
        if not codex:
            return CodexAccountStatus(False, False, "codex CLI not found", str(APP_CODEX_HOME))
        ensure_codex_home()
        proc = subprocess.run(
            [codex, "login", "status"],
            text=True,
            capture_output=True,
            timeout=8,
            env=codex_env(),
        )
        output = ((proc.stdout or "") + (proc.stderr or "")).strip()
        logged_in = proc.returncode == 0 and "not logged in" not in output.lower()
        return CodexAccountStatus(True, logged_in, output or "no status output", str(APP_CODEX_HOME))

    def login_instructions(self) -> dict[str, object]:
        ensure_codex_home()
        return {
            "method": "official-codex-device-auth",
            "codex_home": str(APP_CODEX_HOME),
            "command": "codex login --device-auth",
            "environment": {"CODEX_HOME": str(APP_CODEX_HOME)},
            "notes": [
                "Run through the official Codex CLI device-code flow.",
                "Each user signs in with their own ChatGPT/Codex account.",
                "CopiClin must never read raw Codex tokens or browser cookies.",
                "Installer may bundle or download the official Codex CLI, subject to license/release validation.",
            ],
        }

    def generate_structured_note(self, *_: object, **__: object):
        status = self.status()
        if not status.logged_in:
            raise RuntimeError("Codex account is not logged in for this app user.")
        raise NotImplementedError(
            "Codex account note generation requires a validated official non-interactive Codex CLI/app-server path."
        )
