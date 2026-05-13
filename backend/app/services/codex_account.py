from __future__ import annotations

import subprocess
from dataclasses import dataclass
from shutil import which


@dataclass
class CodexAccountStatus:
    available: bool
    logged_in: bool
    detail: str


class CodexAccountProvider:
    """Experimental account-backed provider using official Codex CLI only.

    This provider must never read raw OAuth tokens, cookies, browser sessions, or
    private endpoints. It only checks/invokes the official `codex` CLI installed
    on the user's machine. For now it is a guarded skeleton, not medical-note
    generation production code.
    """

    provider_id = "codex-account"

    def status(self) -> CodexAccountStatus:
        codex = which("codex")
        if not codex:
            return CodexAccountStatus(False, False, "codex CLI not found")
        proc = subprocess.run([codex, "login", "status"], text=True, capture_output=True, timeout=8)
        output = ((proc.stdout or "") + (proc.stderr or "")).strip()
        logged_in = proc.returncode == 0 and "not logged in" not in output.lower()
        return CodexAccountStatus(True, logged_in, output or "no status output")

    def generate_structured_note(self, *_: object, **__: object):
        status = self.status()
        if not status.logged_in:
            raise RuntimeError("Codex account is not logged in. Use official Codex login first.")
        raise NotImplementedError(
            "Codex account note generation is intentionally not implemented until an official, "
            "documented non-interactive integration path is validated for this medical app."
        )
