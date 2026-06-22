"""Local filesystem storage for uploaded files.

Abstracted behind a tiny interface so it can be swapped for S3/GCS later.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from app.core.config import settings


class FileStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base = Path(base_dir or settings.upload_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, data: bytes) -> str:
        ext = os.path.splitext(filename)[1].lower()
        key = f"{uuid.uuid4().hex}{ext}"
        path = self.base / key
        path.write_bytes(data)
        return str(path)

    def read(self, storage_path: str) -> bytes:
        return Path(storage_path).read_bytes()

    def delete(self, storage_path: str) -> None:
        try:
            Path(storage_path).unlink()
        except FileNotFoundError:
            pass
