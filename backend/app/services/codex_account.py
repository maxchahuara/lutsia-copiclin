from __future__ import annotations

import os
import re
import json
import subprocess
import tempfile
import threading
import uuid
from dataclasses import asdict, dataclass, field
from shutil import which

from app.schemas.clinical_note import ClinicalNoteResult
from app.paths import codex_home_dir

APP_CODEX_HOME = codex_home_dir()
CODEX_CONFIG = (
    "# LUTSIA CopiCLin app-specific Codex config\n"
    "# Credentials are scoped to this Windows user and app data folder.\n"
    'cli_auth_credentials_store = "file"\n'
    'forced_login_method = "chatgpt"\n'
)
AUTH_URL_RE = re.compile(r"https://auth\.openai\.com/\S+")
USER_CODE_RE = re.compile(r"\b[A-Z0-9]{4}-[A-Z0-9]{4,6}\b")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
LOGIN_SESSIONS: dict[str, "CodexLoginSession"] = {}
LOGIN_LOCK = threading.Lock()


@dataclass
class CodexAccountStatus:
    available: bool
    logged_in: bool
    detail: str
    codex_home: str
    auth_scope: str = "per-user app CODEX_HOME"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class CodexLoginSession:
    session_id: str
    started: bool
    message: str
    auth_url: str | None = None
    user_code: str | None = None
    expires_in_minutes: int = 15
    status: str = "starting"
    output: list[str] = field(default_factory=list)
    process: subprocess.Popen[str] | None = field(default=None, repr=False)
    ready: threading.Event = field(default_factory=threading.Event, repr=False)

    def to_dict(self, account_status: CodexAccountStatus | None = None) -> dict[str, object]:
        if account_status and account_status.logged_in:
            self.status = "completed"
        elif self.process and self.process.poll() is not None and self.status not in {"completed", "failed"}:
            self.status = "failed" if self.process.returncode else "completed"
        return {
            "session_id": self.session_id,
            "started": self.started,
            "message": self.message,
            "auth_url": self.auth_url,
            "user_code": self.user_code,
            "expires_in_minutes": self.expires_in_minutes,
            "status": self.status,
            "logged_in": bool(account_status and account_status.logged_in),
        }


def codex_env() -> dict[str, str]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(APP_CODEX_HOME)
    return env


def ensure_codex_home() -> None:
    APP_CODEX_HOME.mkdir(parents=True, exist_ok=True)
    config = APP_CODEX_HOME / "config.toml"
    if not config.exists() or "cli_auth_credentials_store = \"keyring\"" in config.read_text(
        encoding="utf-8"
    ):
        config.write_text(CODEX_CONFIG, encoding="utf-8")


def _status_from_command(codex: str, env: dict[str, str] | None) -> tuple[bool, str]:
    proc = subprocess.run(
        [codex, "login", "status"],
        text=True,
        capture_output=True,
        timeout=8,
        env=env,
    )
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    lower = output.lower()
    logged_in = proc.returncode == 0 and "not logged in" not in lower and "error" not in lower
    return logged_in, output or "no status output"


def parse_device_auth_output(text: str) -> tuple[str | None, str | None]:
    clean_text = ANSI_RE.sub("", text)
    auth_url_match = AUTH_URL_RE.search(clean_text)
    code_match = USER_CODE_RE.search(clean_text)
    return (
        auth_url_match.group(0).rstrip(".,") if auth_url_match else None,
        code_match.group(0) if code_match else None,
    )


def _strict_json_schema(schema: dict) -> dict:
    """Make Pydantic JSON Schema acceptable for strict structured outputs."""
    if schema.get("type") == "object":
        schema.setdefault("additionalProperties", False)
        properties = schema.get("properties")
        if isinstance(properties, dict):
            schema["required"] = list(properties.keys())
    for key in ("properties", "$defs", "definitions"):
        value = schema.get(key)
        if isinstance(value, dict):
            for child in value.values():
                if isinstance(child, dict):
                    _strict_json_schema(child)
    for key in ("items", "anyOf", "allOf", "oneOf"):
        value = schema.get(key)
        if isinstance(value, dict):
            _strict_json_schema(value)
        elif isinstance(value, list):
            for child in value:
                if isinstance(child, dict):
                    _strict_json_schema(child)
    return schema


def _read_login_output(session: CodexLoginSession) -> None:
    proc = session.process
    if not proc or not proc.stdout:
        session.status = "failed"
        session.message = "No se pudo leer el inicio de sesion."
        session.ready.set()
        return

    try:
        for line in proc.stdout:
            clean_line = ANSI_RE.sub("", line.rstrip())
            session.output.append(clean_line)
            auth_url, user_code = parse_device_auth_output("\n".join(session.output))
            if auth_url:
                session.auth_url = auth_url
            if user_code:
                session.user_code = user_code
            if session.auth_url and session.user_code and session.status == "starting":
                session.status = "waiting_for_user"
                session.message = "Codigo listo. Abre OpenAI Codex y confirma el inicio de sesion."
                session.ready.set()
        return_code = proc.wait()
        if return_code == 0:
            session.status = "completed"
            session.message = "Inicio de sesion completado."
        elif session.status != "waiting_for_user":
            session.status = "failed"
            session.message = "No se pudo iniciar sesion con OpenAI Codex."
    except Exception as exc:  # pragma: no cover - background thread
        session.status = "failed"
        session.message = f"No se pudo iniciar sesion: {exc}"
    finally:
        session.ready.set()


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
        try:
            logged_in, output = _status_from_command(codex, codex_env())
        except subprocess.TimeoutExpired:
            return CodexAccountStatus(
                True, False, "codex login status timed out", str(APP_CODEX_HOME)
            )
        except Exception as exc:  # pragma: no cover - platform dependent
            return CodexAccountStatus(
                True, False, f"codex login status failed: {exc}", str(APP_CODEX_HOME)
            )
        if not logged_in:
            try:
                global_logged_in, global_output = _status_from_command(codex, None)
            except Exception:
                global_logged_in = False
                global_output = ""
            if global_logged_in:
                return CodexAccountStatus(
                    True,
                    True,
                    f"Cuenta ChatGPT/Codex detectada en esta PC ({global_output})",
                    str(APP_CODEX_HOME),
                    "existing per-user Codex session",
                )
        return CodexAccountStatus(
            True, logged_in, output or "no status output", str(APP_CODEX_HOME)
        )

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
                "LUTSIA CopiCLin must never read raw Codex tokens or browser cookies.",
                "Installer may bundle or download the official Codex CLI, subject to license/release validation.",
            ],
        }

    def start_login(self) -> dict[str, object]:
        codex = which("codex")
        if not codex:
            return {
                "session_id": "",
                "started": False,
                "message": "No se encontro Codex CLI. El instalador debe incluirlo antes del primer uso.",
                "auth_url": None,
                "user_code": None,
                "expires_in_minutes": 15,
                "status": "failed",
                "logged_in": False,
            }

        ensure_codex_home()
        session = CodexLoginSession(
            session_id=uuid.uuid4().hex,
            started=True,
            message="Preparando inicio de sesion seguro...",
        )
        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            session.process = subprocess.Popen(
                [codex, "login", "--device-auth"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=codex_env(),
                creationflags=creationflags,
            )
        except Exception as exc:  # pragma: no cover - platform dependent
            session.started = False
            session.status = "failed"
            session.message = f"No se pudo iniciar sesion: {exc}"
            return session.to_dict(self.status())

        with LOGIN_LOCK:
            LOGIN_SESSIONS[session.session_id] = session
        threading.Thread(target=_read_login_output, args=(session,), daemon=True).start()
        session.ready.wait(timeout=10)
        return session.to_dict(self.status())

    def login_session(self, session_id: str) -> dict[str, object]:
        with LOGIN_LOCK:
            session = LOGIN_SESSIONS.get(session_id)
        if not session:
            return {
                "session_id": session_id,
                "started": False,
                "message": "Sesion de inicio no encontrada.",
                "auth_url": None,
                "user_code": None,
                "expires_in_minutes": 15,
                "status": "missing",
                "logged_in": self.status().logged_in,
            }
        return session.to_dict(self.status())

    def cancel_login(self, session_id: str) -> dict[str, object]:
        with LOGIN_LOCK:
            session = LOGIN_SESSIONS.pop(session_id, None)
        if not session:
            return {"cancelled": False, "message": "Sesion de inicio no encontrada."}
        if session.process and session.process.poll() is None:
            session.process.terminate()
        session.status = "cancelled"
        session.message = "Inicio de sesion cancelado."
        return {"cancelled": True, "message": session.message}

    def generate_structured_note(
        self, transcript: dict, model_name: str | None = None, timeout_seconds: int = 180
    ) -> ClinicalNoteResult:
        status = self.status()
        if not status.logged_in:
            raise RuntimeError("Codex account is not logged in for this app user.")
        codex = which("codex")
        if not codex:
            raise RuntimeError("codex CLI not found")

        transcript_text = "\n".join(
            f"[{segment.get('id', 'seg')}] {segment.get('speaker_label', 'desconocido')}: "
            f"{segment.get('text', '').strip()}"
            for segment in transcript.get("segments", [])
            if str(segment.get("text", "")).strip()
        )
        if not transcript_text:
            note = ClinicalNoteResult()
            note.metadata.quality_warnings.append("No hay transcripcion suficiente para analizar.")
            note.metadata.missing_information.append("Transcripcion clinica")
            return note

        schema = _strict_json_schema(ClinicalNoteResult.model_json_schema())
        prompt = (
            "Actua como asistente de documentacion clinica para LUTSIA CopiCLin. "
            "Tu tarea es organizar una transcripcion autorizada de entrevista medica en un "
            "borrador estructurado para lectura y revision del medico. No diagnostiques, no "
            "propongas diagnosticos diferenciales, no sugieras tratamientos, no codifiques y no "
            "tomes decisiones clinicas. Solo extrae, resume y ordena informacion mencionada de "
            "forma explicita. Si un diagnostico, medicamento, antecedente, examen o plan fue dicho "
            "por el medico o el paciente, puedes registrarlo como informacion mencionada; si no fue "
            "dicho, usa exactamente 'No mencionado'. No inventes datos. Distingue hechos de "
            "incertidumbres y campos pendientes de confirmacion. Toda salida es borrador y requiere "
            "revision profesional. Incluye trazabilidad con ids de segmentos cuando una seccion use "
            "informacion de la conversacion. Devuelve solamente JSON valido que cumpla el esquema.\n\n"
            f"TRANSCRIPCION:\n{transcript_text}\n"
        )

        with tempfile.TemporaryDirectory(prefix="lutsia-codex-note-") as tmp:
            schema_path = os.path.join(tmp, "clinical_note_schema.json")
            output_path = os.path.join(tmp, "clinical_note_output.json")
            with open(schema_path, "w", encoding="utf-8") as handle:
                json.dump(schema, handle, ensure_ascii=False)

            command = [
                codex,
                "--ask-for-approval",
                "never",
                "exec",
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-rules",
                "--sandbox",
                "read-only",
                "--output-schema",
                schema_path,
                "--output-last-message",
                output_path,
                "-",
            ]
            if model_name and model_name != "codex-account-default":
                command[4:4] = ["--model", model_name]

            run_env = None if status.auth_scope == "existing per-user Codex session" else codex_env()
            proc = subprocess.run(
                command,
                input=prompt.encode("utf-8"),
                capture_output=True,
                timeout=timeout_seconds,
                env=run_env,
                cwd=tmp,
            )
            stdout = (proc.stdout or b"").decode("utf-8", errors="replace")
            stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
            if proc.returncode != 0:
                output = (stdout + "\n" + stderr).strip()
                raise RuntimeError(f"Codex no pudo generar la nota clinica: {output}")

            raw_output = ""
            if os.path.exists(output_path):
                raw_output = open(output_path, encoding="utf-8").read().strip()
            raw_output = raw_output or stdout.strip()
            if raw_output.startswith("```"):
                raw_output = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_output, flags=re.S)
            try:
                payload = json.loads(raw_output)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Codex devolvio una respuesta no JSON para la nota clinica.") from exc

        note = ClinicalNoteResult.model_validate(payload)
        note.metadata.source = "codex-account"
        if "Borrador generado por IA; requiere revision profesional." not in note.metadata.quality_warnings:
            note.metadata.quality_warnings.append(
                "Borrador generado por IA; requiere revision profesional."
            )
        return note
