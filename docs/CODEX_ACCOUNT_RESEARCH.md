# Codex account research for LUTSIA CopiClin

Date: 2026-05-13

## Findings

Official OpenAI Codex documentation says Codex supports two auth modes: ChatGPT sign-in for subscription access and API key for usage-based access. For this product, dr. Max wants ChatGPT/Codex account sign-in, not API-key-first.

The official `openai/codex` repository documents installation through npm, Homebrew, or GitHub Releases binaries, and says users can run Codex and select “Sign in with ChatGPT”. It also documents device-code login for headless/callback-hostile setups via `codex login --device-auth`.

OpenClaw’s OpenAI provider docs separate routes clearly:

- API key direct OpenAI Platform route.
- OpenAI Codex OAuth/subscription route.
- Native Codex app-server harness with `agentRuntime.id: codex`.

Important OpenClaw lesson: do not mix API-key and Codex subscription auth accidentally. OpenClaw also avoids clobbering the user’s real Codex CLI auth by isolating Codex auth homes/harness state in some paths.

## CopiClin decision

Each installed user must authenticate with their own ChatGPT/Codex account. CopiClin must not use dr. Max’s account or the developer machine’s `~/.codex`.

Implementation direction:

- Use official Codex CLI/tooling only.
- Use app-specific `CODEX_HOME` under the user’s app data directory.
- Configure Codex credentials to prefer OS keychain when supported.
- Expose app endpoints to check status and provide login instructions.
- Never read raw tokens, cookies, browser sessions, or private endpoints.
- Do not automate ChatGPT Web.

## Remaining validation needed

Before using Codex for clinical note generation in production, validate an official non-interactive path suitable for a packaged desktop app, likely one of:

1. Bundled official Codex CLI invoked with app-scoped `CODEX_HOME`.
2. Official Codex app-server/local harness if documented for embedding.
3. OpenClaw-style provider/auth architecture if reusable under license and product constraints.

The current code intentionally implements status/login scaffolding and fails closed for actual note generation until that integration is validated.
