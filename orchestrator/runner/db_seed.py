from __future__ import annotations

from sqlalchemy.orm import Session

from runner.integrations.registry import seed_integration_defaults


def seed_database(session: Session) -> None:
    seed_integration_defaults(session)
