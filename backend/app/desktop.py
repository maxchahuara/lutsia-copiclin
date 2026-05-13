from __future__ import annotations

import socket
import threading
import time

import uvicorn
import webview

from app.main import app


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run_api(host: str, port: int) -> None:
    uvicorn.run(app, host=host, port=port, log_level="warning")


def main() -> None:
    host = "127.0.0.1"
    port = _free_local_port()
    threading.Thread(target=run_api, args=(host, port), daemon=True).start()
    time.sleep(1.0)
    webview.create_window("LUTSIA CopiClin", f"http://{host}:{port}/", width=1200, height=800)
    webview.start()


if __name__ == "__main__":
    main()
