# Install

## Developer/source install

Requirements:

- Python 3.11+
- Node.js 22+
- npm

```bash
make setup
make check
```

Run backend and API docs:

```bash
make dev-backend
```

Run frontend dev server:

```bash
make dev-frontend
```

Build static frontend into the Python app:

```bash
make frontend-build
```

Then run:

```bash
. .venv/bin/activate
lutsia-copiclin-api
# or
lutsia-copiclin-desktop
```

## Local transcription packages

```bash
scripts/bootstrap_local_ai.sh
```

The app uses `imageio-ffmpeg` so packaged builds can include FFmpeg support without requiring physicians to install system FFmpeg manually. Large The default local Whisper model (`small`) is downloaded during setup. Larger Whisper model downloads are intentionally not automatic; the UI must ask for explicit model selection/download consent.

## Codex account provider

End users must authenticate with their own ChatGPT/Codex account. The app must not use developer credentials.

Use `/auth/codex/login-instructions` to obtain the exact app-scoped `CODEX_HOME` and run official Codex device authentication for that user.

## End-user installers

Future releases should provide OS installers from GitHub Releases. The installer must bundle or install:

- Python runtime/backend.
- Desktop shell.
- Built frontend assets.
- Audio conversion support.
- Optional official Codex CLI integration, subject to license and release validation.

Before publishing an installer, run `make check` on Linux, Windows, and macOS CI.
