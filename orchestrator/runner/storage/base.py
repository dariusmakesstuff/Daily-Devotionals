from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ObjectStorage(Protocol):
    """GCS / S3 / local — store run artifacts (audio, video, transcripts)."""

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        """Persist object; return URI or path reference."""
        ...

    def public_url(self, key: str) -> str | None:
        """Signed or public URL if applicable."""
        ...
