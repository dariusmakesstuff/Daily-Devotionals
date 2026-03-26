from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _headers(service_key: str) -> dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def fetch_editorial_calendar_preview(base_url: str, service_key: str, limit: int = 5) -> list[dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/rest/v1/editorial_calendar"
    params = {
        "select": "id,month_start,theme_title,theme_summary,scripture_anchors,tone_notes",
        "order": "month_start.desc",
        "limit": str(limit),
    }
    with httpx.Client(timeout=45.0) as client:
        r = client.get(url, params=params, headers=_headers(service_key))
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            logger.warning("unexpected editorial_calendar shape: %s", type(data))
            return []
        return data


def fetch_character_canon(
    base_url: str,
    service_key: str,
    character_id: str,
) -> dict[str, Any] | None:
    url = f"{base_url.rstrip('/')}/rest/v1/character_canon"
    params = {
        "select": "character_id,character_name,facts_json,canon_summary,open_threads_json,forbidden_retcon_json,updated_at",
        "character_id": f"eq.{character_id}",
        "limit": "1",
    }
    with httpx.Client(timeout=45.0) as client:
        r = client.get(url, params=params, headers=_headers(service_key))
        r.raise_for_status()
        rows = r.json()
        if not isinstance(rows, list) or not rows:
            return None
        return rows[0]


def fetch_latest_character_episode(
    base_url: str,
    service_key: str,
    character_id: str,
) -> dict[str, Any] | None:
    url = f"{base_url.rstrip('/')}/rest/v1/character_episodes"
    params = {
        "select": "run_id,ministry_date,character_id,arc_note,episode_snapshot",
        "character_id": f"eq.{character_id}",
        "order": "ministry_date.desc",
        "limit": "1",
    }
    with httpx.Client(timeout=45.0) as client:
        r = client.get(url, params=params, headers=_headers(service_key))
        r.raise_for_status()
        rows = r.json()
        if not isinstance(rows, list) or not rows:
            return None
        return rows[0]
