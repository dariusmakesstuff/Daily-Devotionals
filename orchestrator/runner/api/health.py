from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from runner.db import get_db
from runner.integrations.registry import IntegrationRegistry

router = APIRouter(tags=["health"])
Db = Annotated[Session, Depends(get_db)]


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/integrations")
def health_integrations(db: Db) -> dict:
    """Integration toggle snapshot for ops dashboards (no secrets)."""
    reg = IntegrationRegistry.load(db)
    return {"status": "ok", "integrations": reg.snapshot()}
