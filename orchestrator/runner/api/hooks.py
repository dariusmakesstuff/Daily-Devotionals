from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from runner.api.deps import require_operator_api_key
from runner.db import get_db
from runner.models_extended import Notification, NotificationStatus
from runner.schemas import WebhookEventIn

router = APIRouter(prefix="/hooks", tags=["hooks"])
Db = Annotated[Session, Depends(get_db)]


@router.post("/run-completed", status_code=202, dependencies=[Depends(require_operator_api_key)])
def hook_run_completed(body: WebhookEventIn, db: Db) -> dict:
    """Queue outbound automation (n8n hybrid / Zapier). Sender processes `notifications` table."""
    n = Notification(
        id=uuid.uuid4(),
        run_id=body.run_id,
        channel="webhook",
        payload={"event": body.event, **(body.payload or {})},
        status=NotificationStatus.pending.value,
    )
    db.add(n)
    db.commit()
    return {"queued_notification_id": str(n.id)}


@router.post("/n8n/trigger", status_code=202, dependencies=[Depends(require_operator_api_key)])
def hook_n8n_trigger(body: WebhookEventIn, db: Db) -> dict:
    """Inbound contract for optional n8n sidecar — stores payload for workers or external pollers."""
    n = Notification(
        id=uuid.uuid4(),
        run_id=body.run_id,
        channel="n8n_trigger",
        payload={"event": body.event, **(body.payload or {})},
        status=NotificationStatus.pending.value,
    )
    db.add(n)
    db.commit()
    return {"queued_notification_id": str(n.id)}
