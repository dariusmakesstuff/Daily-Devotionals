"""S3-compatible uploads via presigned PUT or PutObject (optional boto3)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class S3CompatStorage:
    """Wire `boto3` in production; constructor accepts client factory."""

    def __init__(self, bucket: str, **kwargs: Any) -> None:
        self.bucket = bucket
        self._kwargs = kwargs

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        try:
            import boto3
        except ImportError as e:
            raise RuntimeError("boto3 required for S3CompatStorage") from e
        client = boto3.client("s3", **self._kwargs)
        extra: dict = {}
        if content_type:
            extra["ContentType"] = content_type
        client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        return f"s3://{self.bucket}/{key}"

    def public_url(self, key: str) -> str | None:
        return None
