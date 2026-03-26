from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from runner.api.deps import require_operator_api_key
from runner.db import get_db
from runner.integrations.registry import DEFAULT_FLAGS, IntegrationRegistry
from runner.models_extended import IntegrationSetting
from runner.schemas import IntegrationOut, IntegrationPatch

router = APIRouter(prefix="/integrations", tags=["integrations"])
Db = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[IntegrationOut])
def list_integrations(db: Db) -> list[IntegrationOut]:
    reg = IntegrationRegistry.load(db)
    snap = reg.snapshot()
    rows = {r.key: r for r in db.execute(select(IntegrationSetting)).scalars().all()}
    out: list[IntegrationOut] = []
    for key in sorted(set(DEFAULT_FLAGS) | set(rows.keys())):
        row = rows.get(key)
        out.append(
            IntegrationOut(
                key=key,
                enabled=snap.get(key, DEFAULT_FLAGS.get(key, False)),
                health_ok=row.health_ok if row else None,
                config=row.config if row else None,
            )
        )
    return out


@router.patch("/{key}", response_model=IntegrationOut, dependencies=[Depends(require_operator_api_key)])
def patch_integration(key: str, body: IntegrationPatch, db: Db) -> IntegrationOut:
    row = db.get(IntegrationSetting, key)
    if not row:
        row = IntegrationSetting(key=key, enabled=body.enabled)
        db.add(row)
    else:
        row.enabled = body.enabled
    db.commit()
    db.refresh(row)
    return IntegrationOut(key=row.key, enabled=row.enabled, health_ok=row.health_ok, config=row.config)
