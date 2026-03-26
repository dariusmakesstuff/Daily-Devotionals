"""Integration registry: DB-backed toggles with safe defaults (disabled integrations skip, never crash runs)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from runner.models_extended import IntegrationSetting

# Keys referenced by `integration_policy` and seeds.
DEFAULT_FLAGS: dict[str, bool] = {
    "llm": True,
    "supabase": True,
    "tts": True,
    "veo": False,
    "publish": False,
    "media_assembly": True,
    "engagement": False,
    "slack": False,
    "email": False,
    "gcs": False,
    "s3": False,
    "shotstack": False,
}


@dataclass
class IntegrationRegistry:
    """Resolved enablement: explicit DB row wins; else default."""

    states: dict[str, bool] = field(default_factory=dict)

    def enabled(self, key: str) -> bool:
        if key in self.states:
            return bool(self.states[key])
        return bool(DEFAULT_FLAGS.get(key, False))

    @classmethod
    def load(cls, session: Session) -> IntegrationRegistry:
        rows = session.execute(select(IntegrationSetting)).scalars().all()
        states = {r.key: bool(r.enabled) for r in rows}
        return cls(states=states)

    def snapshot(self) -> dict[str, Any]:
        out = dict(DEFAULT_FLAGS)
        out.update(self.states)
        return out


def seed_integration_defaults(session: Session) -> None:
    """Idempotent: insert missing integration rows with defaults."""
    existing = {r.key for r in session.execute(select(IntegrationSetting)).scalars().all()}
    for key, enabled in DEFAULT_FLAGS.items():
        if key not in existing:
            session.add(IntegrationSetting(key=key, enabled=enabled))
    session.commit()
