from __future__ import annotations

import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from runner.api.deps import require_operator_api_key
from runner.db import get_db
from runner.models_extended import EngagementRun
from runner.pipeline.engagement_definition import steps_for_engagement_run
from runner.pipeline.engagement_runner import execute_engagement_sync
from runner.schemas import EngagementRunCreate, EngagementRunOut

router = APIRouter(prefix="/engagement-runs", tags=["engagement"])
Db = Annotated[Session, Depends(get_db)]


def _to_out(run: EngagementRun) -> EngagementRunOut:
    return EngagementRunOut.model_validate(run)


async def _enqueue_engagement(request: Request, run_id: uuid.UUID) -> None:
    pool = request.app.state.arq_pool
    if pool is not None:
        await pool.enqueue_job("process_engagement_run", str(run_id))
    else:
        await asyncio.to_thread(execute_engagement_sync, run_id)


@router.post("", response_model=EngagementRunOut, dependencies=[Depends(require_operator_api_key)])
async def create_engagement_run(
    body: EngagementRunCreate,
    request: Request,
    db: Db,
) -> EngagementRunOut:
    if body.idempotency_key:
        existing = db.execute(
            select(EngagementRun).where(EngagementRun.idempotency_key == body.idempotency_key)
        ).scalar_one_or_none()
        if existing:
            run = db.execute(
                select(EngagementRun)
                .options(selectinload(EngagementRun.steps))
                .where(EngagementRun.id == existing.id)
            ).scalar_one()
            return _to_out(run)

    cid = body.correlation_id or str(uuid.uuid4())
    run = EngagementRun(
        idempotency_key=body.idempotency_key,
        meta=body.meta,
        correlation_id=cid,
        status="queued",
    )
    for s in steps_for_engagement_run():
        run.steps.append(s)
    db.add(run)
    db.commit()
    db.refresh(run)

    await _enqueue_engagement(request, run.id)

    db.expire_all()
    run = db.execute(
        select(EngagementRun).options(selectinload(EngagementRun.steps)).where(EngagementRun.id == run.id)
    ).scalar_one()
    return _to_out(run)


@router.get("", response_model=list[EngagementRunOut])
def list_engagement_runs(db: Db, limit: int = 50) -> list[EngagementRunOut]:
    runs = (
        db.execute(
            select(EngagementRun)
            .options(selectinload(EngagementRun.steps))
            .order_by(EngagementRun.created_at.desc())
            .limit(min(limit, 200))
        )
        .scalars()
        .all()
    )
    return [_to_out(r) for r in runs]


@router.get("/{run_id}", response_model=EngagementRunOut)
def get_engagement_run(run_id: uuid.UUID, db: Db) -> EngagementRunOut:
    run = db.execute(
        select(EngagementRun).options(selectinload(EngagementRun.steps)).where(EngagementRun.id == run_id)
    ).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="engagement run not found")
    return _to_out(run)
