# LUTSIA CopiClin - AI provider strategy

Status: revised after owner direction
Date: 2026-05-13

## Product direction

LUTSIA CopiClin should behave like an agile clinical copilot, not a restrictive/expensive API-first tool.

Owner direction: prefer a ChatGPT/Codex-account style provider similar in spirit to OpenClaw, and do not make OpenAI API keys the required/default path.

## Non-negotiable boundary

The app must not automate ChatGPT web, extract cookies, use private endpoints, simulate browser sessions, or depend on hacks.

## Recommended interpretation

The acceptable path is an **official local account-backed provider** only when it uses documented OpenAI/Codex tooling/authentication, similar to how OpenClaw/Codex CLI can authenticate with ChatGPT/Codex accounts.

For MVP development, implement provider abstraction with:

1. `MockProvider` for deterministic dev/tests.
2. `LocalProvider` adapters for local Ollama / faster-whisper / whisper.cpp.
3. `CodexAccountProvider` as an experimental local bridge that invokes an officially authenticated Codex CLI or documented local OpenAI tooling, if present on the user's machine.
4. `OpenAIAPIProvider` not as the default path; keep it optional/disabled behind explicit configuration only if later accepted.

## CodexAccountProvider constraints

- Must rely only on official documented tooling/auth.
- Must not read or copy raw OAuth tokens.
- Must not expose secrets in logs.
- Must not run arbitrary untrusted commands.
- Must present clear UX: “Uses your locally authenticated Codex/OpenAI account if available.”
- Must provide fallback to local/offline providers.
- Must be documented as experimental until confirmed stable for packaged end-user use.

## Medical/privacy note

Using an account-backed cloud model still sends consultation text/audio-derived content to a third-party AI service. The UI must disclose this clearly. Local/offline mode remains the privacy-first option.
