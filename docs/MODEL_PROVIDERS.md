# Model providers

Current product decision from dr. Max: **no local LLM for now**. The LLM/cerebro path should be OpenAI Codex account login, similar in spirit to OpenClaw, and not OpenAI API-key-first.

## Enabled direction

- `codex-account`: primary intended LLM provider. It may use only official documented Codex/OpenAI local tooling and account login. It must never read raw OAuth tokens, cookies, browser sessions, or private endpoints.
- `mock`: development/test provider only so the app and tests run deterministically without sending clinical data anywhere.

## Transcription

Local Whisper/faster-whisper may still be used for **transcription**. This is not a local LLM. It supports the privacy-first goal for audio-to-text.

## Disabled for now

- Ollama/local LLMs: intentionally not used at this stage.
- OpenAI API-key-first flow: intentionally not the default product path.
- ChatGPT web automation: forbidden.
- Cookies/private endpoints/browser session hacks: forbidden.
