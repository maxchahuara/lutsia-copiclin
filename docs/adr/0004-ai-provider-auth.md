# ADR 0004: AI provider auth

Decision: use OpenAI Codex account login as the intended LLM/cerebro path, using only official documented, app-scoped Codex tooling.

Rejected for now:

- Local LLMs such as Ollama.
- OpenAI API-key-first product flow.
- ChatGPT web automation.
- Cookies/private endpoints/browser session hacks.

Mock provider remains for deterministic tests only.
