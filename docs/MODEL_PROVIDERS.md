# Model providers

Provider abstraction is mandatory. Current implemented providers:

- `MockTranscriptionProvider`: deterministic development/testing.
- `MockLLMProvider`: returns valid clinical JSON with `No mencionado` defaults.
- `LocalFasterWhisperProvider`: optional local Whisper implementation, enabled after installing `.[local-ai]` and selecting/downloading a model.

Planned providers:

- `LocalOllamaProvider` for local LLMs.
- `CodexAccountProvider` experimental: may use only official documented local Codex/OpenAI tooling/auth. It must never read raw tokens, cookies, browser sessions, or private endpoints.

OpenAI API key is not default. If ever enabled, it must be explicit, optional, keychain-backed, and clearly disclosed.
