# LUTSIA CopiClin - Initial Architecture Plan

Date: 2026-05-13
Status: pre-development plan

## 1. Understanding

LUTSIA CopiClin is a local-first desktop assistant for physicians. It records or imports consultation audio, stores data locally, transcribes speech, structures clinical information in Spanish, and produces editable/copyable clinical documentation blocks. It is not an EHR, not a diagnostic medical device, and not an autonomous clinical decision system.

Core product priorities:

1. Local privacy and no proprietary cloud backend.
2. One-click install from GitHub Releases for Windows, macOS, and Linux.
3. Simple workflow for non-technical physicians.
4. Official/allowed AI integrations only.
5. Provider abstraction for OpenAI API and local models.
6. Traceability from generated note sections back to transcript segments.
7. Medical safety: no invented facts, explicit uncertainty, physician validation required.

## 2. OpenAI integration validation

Validated from official OpenAI developer docs on 2026-05-13:

- Official Speech-to-Text API supports transcriptions, including `whisper-1`, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, and `gpt-4o-transcribe-diarize` where available. File upload limit is documented as 25 MB for bounded file requests; formats include mp3/mp4/mpeg/mpga/m4a/wav/webm.
- Official Structured Outputs supports JSON Schema / Pydantic parsing through the OpenAI API.
- Codex has official authentication for Codex CLI/IDE/cloud, including ChatGPT sign-in and API key, but this is documented for Codex tooling, not as a general third-party desktop app provider for medical note generation.

Decision for MVP:

- OpenAI provider: official OpenAI API key only.
- Store API key in OS keychain via `keyring`.
- Do not automate ChatGPT web.
- Do not use cookies/private endpoints/browser sessions.
- `OptionalCodexOrChatGPTProvider` remains disabled and documented as unsupported unless OpenAI documents a permitted product integration for this use case.

## 3. Recommended architecture

Desktop:

- Python 3.11/3.12.
- pywebview shell.
- FastAPI local backend bound to localhost random port.
- React + TypeScript + Vite + Tailwind + shadcn/ui frontend.
- Frontend loaded in pywebview window.

Backend:

- FastAPI + Pydantic.
- SQLModel or SQLAlchemy + SQLite.
- Local job queue using SQLite + threads/asyncio.
- keyring for API keys/master secrets.
- cryptography for app-level file encryption where practical.
- ffmpeg bundled or managed in packaged build.

Providers:

- TranscriptionProvider interface.
- LLMProvider interface.
- OpenAI official providers.
- Local faster-whisper/Ollama providers.
- Mock providers for tests and offline dev.

Data:

- Local app data directory per OS.
- SQLite metadata DB.
- Audio/transcript/note files under per-consultation folders.
- No clinical content in logs.

Packaging:

- PyInstaller first for MVP due ecosystem maturity with Python desktop packaging.
- Nuitka ADR remains open for later performance/obfuscation/smaller binary evaluation.
- GitHub Actions matrix builds on Windows/macOS/Linux; no cross-compilation assumptions.

## 4. Key risks

Technical:

- Cross-platform microphone capture and permissions.
- Packaging ML/audio dependencies with acceptable installer size.
- ffmpeg bundling/licensing/platform differences.
- pywebview + local FastAPI lifecycle reliability.
- Local diarization quality in Spanish.
- App signing/notarization complexity for macOS/Windows.

Medical/legal:

- Medical data sensitivity and consent.
- Risk of hallucinated clinical facts.
- Risk user mistakes generated draft for validated record.
- Country-specific privacy obligations, especially Peru and future jurisdictions.
- App must avoid claiming full legal compliance or diagnostic device status.

Security/privacy:

- API keys must never be plaintext.
- Local files require encryption strategy and clear retention/deletion.
- Logs and crash reports must avoid sensitive content.
- OpenAI mode necessarily sends selected audio/text to OpenAI API; UI must disclose this clearly.

## 5. Decisions requiring approval

1. License: Apache-2.0 recommended for adoption; AGPL-3.0 if forcing open derivatives is more important.
2. Default GitHub repo visibility for early work: private recommended.
3. MVP transcription default: OpenAI API first for accuracy and speed, plus mock/local architecture; or local-only first for privacy purity.
4. Packaging priority order: Windows first, then macOS, then Linux; or all three from day one.
5. Encryption scope for MVP: encrypt API keys only + app-level encrypted files, or postpone full DB/file encryption behind settings.
6. Whether to include local faster-whisper packaged in MVP installer or require user to enable/install local model separately in v0.

## 6. Phased plan

Phase 0 - Repo foundation:

- Monorepo structure.
- Backend/frontend skeleton.
- Docs and ADRs.
- CI baseline.

Phase 1 - Vertical prototype:

- Desktop window opens.
- Backend health/settings.
- Create consultation.
- Record/upload audio.
- Mock transcription + optional OpenAI transcription.
- Mock/OpenAI note generation with Pydantic schema.
- Editable UI and copy summary.

Phase 2 - Privacy/security baseline:

- keyring API key storage.
- Local data directory and retention settings.
- Consent screen.
- Audit events without clinical content.
- Delete consultation including derivatives.

Phase 3 - Real transcription and exports:

- faster-whisper provider.
- OpenAI transcription provider.
- Timestamps and segment editing.
- Markdown/TXT/JSON/PDF export.

Phase 4 - Packaging:

- PyInstaller desktop app.
- Windows installer.
- macOS/Linux packages.
- GitHub Actions release workflow.

Phase 5 - Safety/quality:

- Synthetic test cases.
- Negation/dose/temporal tests.
- JSON validity tests.
- UI smoke tests.

## 7. Effort estimate

- Repo/CI/docs foundation: 1-2 days.
- Desktop shell + backend lifecycle: 2-4 days.
- Frontend MVP flow: 4-7 days.
- Audio capture/upload/chunking: 3-6 days.
- Transcription providers: 3-7 days initial, more for robust local packaging.
- LLM providers/schema/safety prompts: 3-5 days.
- Storage/encryption/keyring/audit: 3-6 days.
- Export formats: 2-4 days.
- Packaging per OS: 5-12 days total depending signing/notarization.
- Test suite and synthetic evaluation: 4-8 days.

## 8. Stack final recommended

- Python 3.11 initially.
- FastAPI, Pydantic v2, SQLModel or SQLAlchemy 2.
- SQLite.
- keyring, cryptography.
- pywebview.
- React, TypeScript, Vite.
- Tailwind + shadcn/ui.
- TanStack Query + Zustand if needed.
- pytest, ruff, mypy/pyright optional.
- Vitest + Playwright.
- PyInstaller first.
- GitHub Actions matrix.

## 9. First 2-week milestone

Goal: safe vertical MVP in dev mode.

Week 1:

- Repo structure and docs/ADRs.
- Backend FastAPI skeleton.
- DB models and migrations/basic create/read.
- Clinical JSON schema and Pydantic models.
- Mock transcription and mock LLM provider.
- Frontend routes: onboarding, dashboard, new consultation, note view.
- Desktop shell opens frontend.

Week 2:

- Audio recording/upload proof of concept.
- OpenAI API key storage through keyring.
- OpenAI transcription provider.
- OpenAI structured note provider.
- Editable generated note with copy buttons.
- Consent/disclaimer UI.
- Basic exports: TXT/Markdown/JSON.
- Initial tests and CI.

Acceptance for milestone:

- `make dev` starts backend/frontend/desktop dev flow.
- User can create a consultation, record or upload a short audio, transcribe/generate via mock or OpenAI, edit output, and copy summary.
- No credential plaintext.
- No cloud backend.
- No unsupported ChatGPT web automation.
