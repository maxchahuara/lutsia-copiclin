from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile

DATA_ROOT = Path.home() / ".local" / "share" / "lutsia-copiclin" / "consultations"


async def save_upload(consultation_id: str, upload: UploadFile) -> dict[str, object]:
    safe_suffix = Path(upload.filename or "audio.webm").suffix or ".webm"
    dest_dir = DATA_ROOT / consultation_id / "audio"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{uuid4()}{safe_suffix}"
    size = 0
    with dest.open("wb") as fh:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            fh.write(chunk)
    return {
        "path": str(dest),
        "filename": upload.filename,
        "content_type": upload.content_type,
        "size_bytes": size,
        "encrypted": False,
    }
