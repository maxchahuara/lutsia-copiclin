import threading
import time
import webview
import uvicorn
from app.main import app


def run_api() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")


def main() -> None:
    threading.Thread(target=run_api, daemon=True).start()
    time.sleep(0.8)
    webview.create_window("LUTSIA CopiClin", "http://127.0.0.1:8765/health", width=1200, height=800)
    webview.start()


if __name__ == "__main__":
    main()
