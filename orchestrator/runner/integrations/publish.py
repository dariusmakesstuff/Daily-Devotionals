"""Social publish adapters (Upload Post, native APIs) — stubs until credentials wired."""

from __future__ import annotations

from typing import Any


def publish_youtube_stub(title: str, description: str, asset_uri: str) -> dict[str, Any]:
    return {"platform": "youtube", "stub": True, "title": title[:80], "asset_uri": asset_uri[:120]}


def publish_upload_post_stub(platforms: list[str], asset_uri: str) -> dict[str, Any]:
    return {"platforms": platforms, "stub": True, "asset_uri": asset_uri[:120]}


def publish_tiktok_stub(caption: str, asset_uri: str) -> dict[str, Any]:
    return {"platform": "tiktok", "stub": True, "caption": caption[:100], "asset_uri": asset_uri[:120]}
