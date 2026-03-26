import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from runner.db import get_db
from runner.models import OutputMode, Run, RunStatus, StepStatus
from runner.pipeline.definition import steps_for_new_run
from runner.pipeline.runner import execute_run_sync
from runner.schemas import RunCreate, RunOut

router = APIRouter(prefix="/runs", tags=["runs"])

Db = Annotated[Session, Depends(get_db)]

_BOOL_META = (
    "youtube_synthetic_media_disclosure",
    "ai_generated_content",
    "kids_directed",
)


def _validate_run_meta(meta: dict | None) -> None:
    if not meta:
        return
    for k in _BOOL_META:
        if k not in meta:
            continue
        v = meta[k]
        if v is not None and not isinstance(v, bool):
            raise HTTPException(status_code=400, detail=f"meta.{k} must be a boolean or null")


def _to_run_out(run: Run) -> RunOut:
    return RunOut.model_validate(run)


async def _enqueue_or_run_inline(request: Request, run_id: uuid.UUID) -> None:
    pool = request.app.state.arq_pool
    if pool is not None:
        await pool.enqueue_job("process_run", str(run_id))
    else:
        await asyncio.to_thread(execute_run_sync, run_id)


@router.post("", response_model=RunOut)
async def create_run(
    body: RunCreate,
    request: Request,
    db: Db,
) -> RunOut:
    _validate_run_meta(body.meta)
    if body.idempotency_key:
        existing = db.execute(
            select(Run).where(Run.idempotency_key == body.idempotency_key)
        ).scalar_one_or_none()
        if existing:
            run = db.execute(
                select(Run)
                .options(selectinload(Run.steps))
                .where(Run.id == existing.id)
            ).scalar_one()
            return _to_run_out(run)

    mode = OutputMode(body.output_mode.value)
    cid = body.correlation_id or str(uuid.uuid4())
    run = Run(
        output_mode=mode,
        idempotency_key=body.idempotency_key,
        correlation_id=cid,
        meta=body.meta,
        status=RunStatus.queued,
    )
    for step in steps_for_new_run(mode):
        run.steps.append(step)
    db.add(run)
    db.commit()
    db.refresh(run)

    await _enqueue_or_run_inline(request, run.id)

    db.expire_all()
    run = db.execute(
        select(Run).options(selectinload(Run.steps)).where(Run.id == run.id)
    ).scalar_one()
    return _to_run_out(run)


@router.get("", response_model=list[RunOut])
def list_runs(db: Db, limit: int = 50) -> list[RunOut]:
    runs = (
        db.execute(
            select(Run)
            .options(selectinload(Run.steps))
            .order_by(Run.created_at.desc())
            .limit(min(limit, 200))
        )
        .scalars()
        .all()
    )
    return [_to_run_out(r) for r in runs]


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: uuid.UUID, db: Db) -> RunOut:
    run = db.execute(
        select(Run).options(selectinload(Run.steps)).where(Run.id == run_id)
    ).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return _to_run_out(run)


@router.post("/{run_id}/resume", response_model=RunOut)
async def resume_run(run_id: uuid.UUID, request: Request, db: Db) -> RunOut:
    """Clear waiting_human on the current step and re-queue the worker (Slack-approval parity)."""
    run = db.execute(
        select(Run).options(selectinload(Run.steps)).where(Run.id == run_id)
    ).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    if run.status != RunStatus.waiting_human:
        raise HTTPException(status_code=400, detail="run is not waiting for human")

    for step in run.steps:
        if step.status == StepStatus.waiting_human:
            step.status = StepStatus.pending
            step.started_at = None
            break
    run.status = RunStatus.queued
    db.commit()

    await _enqueue_or_run_inline(request, run.id)

    db.expire_all()
    run = db.execute(
        select(Run).options(selectinload(Run.steps)).where(Run.id == run_id)
    ).scalar_one()
    return _to_run_out(run)
