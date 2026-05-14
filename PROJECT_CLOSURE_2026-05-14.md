# Project closure: LUTSIA CopiClin

Date: 2026-05-14

Closed by request of dr. Max to avoid mixing context with future orders.

## Final state at closure

Repository: https://github.com/maxchahuara/lutsia-copiclin
Visibility: public / open source
License: MIT
Branch: main

Latest pushed changes before closure:

- First-run setup checklist added.
- Per-user Codex/ChatGPT account setup flow surfaced.
- Whisper/faster-whisper made local-first and installed during setup.
- Default transcription provider changed to local `faster-whisper`.
- `make setup` downloads/verifies local Whisper model `small`.
- Tests/build/checks passed before push.

## Important continuation rules

- Treat any future project as isolated unless dr. Max explicitly asks to resume CopiClin.
- Do not mix CopiClin assumptions, code, strategy, or product decisions into a new project.
- If dr. Max resumes CopiClin, first pull the public repo and re-check current state.
- Transcription must remain local-only; do not add transcription APIs unless dr. Max explicitly changes that requirement.
- Codex/ChatGPT account usage must remain per end-user; never use dr. Max/LUTSIA credentials for installed users.

