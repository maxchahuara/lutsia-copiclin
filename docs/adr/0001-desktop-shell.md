# ADR 0001: Desktop shell

Decision: start with Python pywebview. It keeps one Python runtime for backend/desktop and avoids Electron size. Tauri remains attractive but adds Rust/webview packaging complexity. Electron is mature but heavier.
