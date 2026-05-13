from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException, UploadFile

from app.paths import consultations_dir

DATA_ROOT = consultations_dir()
MAX_UPLOAD_BYTES = 250 * 1024 * 1024
ALLOWED_AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".webm", ".flac", ".mp4"}


async def save_upload(consultation_id: str, upload: UploadFile) -> dict[str, object]:
    safe_suffix = Path(upload.filename or "audio.webm").suffix.lower() or ".webm"
    if safe_suffix not in ALLOWED_AUDIO_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported audio file type: {safe_suffix}")
    dest_dir = DATA_ROOT / consultation_id / "audio"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{uuid4()}{safe_suffix}"
    size = 0
    with dest.open("wb") as fh:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Audio upload exceeds 250 MB limit")
            fh.write(chunk)
    return {
        "path": str(dest),
        "filename": upload.filename,
        "content_type": upload.content_type,
        "size_bytes": size,
        "encrypted": False,
    }
