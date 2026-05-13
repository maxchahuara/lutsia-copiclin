# LUTSIA CopiClin - AI provider strategy

Status: revised after owner direction
Date: 2026-05-13

## Product direction

LUTSIA CopiClin should use an OpenAI Codex/ChatGPT account login style similar to OpenClaw, not an OpenAI API-key-first flow and not a local LLM for now.

## Non-negotiable boundary

The app must not automate ChatGPT web, extract cookies, use private endpoints, simulate browser sessions, or depend on hacks.

## Current provider policy

1. `CodexAccountProvider` is the intended primary LLM provider. It may use only official documented, app-scoped Codex tooling/authentication.
2. `MockProvider` remains available for tests/dev only.
3. Local Whisper/faster-whisper remains allowed for transcription, not LLM reasoning.
4. Ollama/local LLMs are disabled for now.
5. OpenAI API-key-first flow is not the product default and should not be required for normal use.

## CodexAccountProvider constraints

- Must rely only on official documented tooling/auth.
- Must not read or copy raw OAuth tokens.
- Must not expose secrets in logs.
- Must not run arbitrary untrusted commands.
- Must show clear UX: “Uses your app-scoped authenticated Codex account if available.”
- Must fail closed if Codex is not logged in.

## Current verification note

The code can detect Codex CLI presence and `codex login status`. If the local Codex CLI is not logged in, the provider is unavailable until official login is completed.
