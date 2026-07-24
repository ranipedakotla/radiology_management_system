from __future__ import annotations
from pathlib import Path
from typing import Protocol, Optional


class StorageBackend(Protocol):
    def save_bytes(self, rel_path: str, data: bytes) -> str:
        """Save bytes and return absolute local path or a URL (depending on backend)."""
        ...

    def url_for(self, rel_path: str) -> Optional[str]:
        """Return a public URL if available (S3), else None/local path."""
        ...


class LocalStorage(StorageBackend):
    """
    Saves files under ./static/ and returns absolute file paths.
    Later you can replace this with S3Storage without touching business logic.
    """
    def __init__(self, base_dir: str = "static"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, rel_path: str, data: bytes) -> str:
        dest = (self.base / rel_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return str(dest)

    def url_for(self, rel_path: str) -> Optional[str]:
        # Local dev: no public URL. You can mount /static in FastAPI if you want.
        return None


# Placeholder for later (when you share S3 creds)
class S3Storage(StorageBackend):
    def __init__(self, bucket: str, base_prefix: str = ""):
        # import boto3 here later when you're ready
        self.bucket = bucket
        self.base_prefix = base_prefix.strip("/")

    def save_bytes(self, rel_path: str, data: bytes) -> str:
        raise NotImplementedError("Enable after S3 credentials are available.")

    def url_for(self, rel_path: str) -> Optional[str]:
        # Return the S3 object URL once implemented.
        return None
