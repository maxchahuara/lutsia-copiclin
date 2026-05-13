# Architecture

LUTSIA CopiClin is local-first: pywebview desktop shell, localhost FastAPI backend, React/Vite frontend, SQLite persistence, provider interfaces for transcription and LLM.

Current LLM direction: OpenAI Codex account login via official documented local tooling only. No local LLM for now. No API-key-first requirement. No ChatGPT web automation, cookies, private endpoints, or browser session hacks.

Local Whisper/faster-whisper may be used for transcription.
