"""
Synchronous pipeline execution (invoked from Arq worker via asyncio.to_thread).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from runner.config import get_settings
from runner.db import get_session_factory
from runner.integrations.llm_usage import usage_scope
from runner.integrations.registry import IntegrationRegistry
from runner.models import Run, RunStatus, RunStep, StepStatus
from runner.models_extended import ProviderUsage
from runner.pipeline.definition import STAGES, StageDef
from runner.pipeline.integration_policy import skip_reason_for_stage
from runner.pipeline.stage_handlers import execute_stage

logger = logging.getLogger(__name__)


def _stage_map() -> dict[str, StageDef]:
    return {s.key: s for s in STAGES}


def execute_run_sync(run_id: uuid.UUID) -> None:
    settings = get_settings()
    factory = get_session_factory()
    smap = _stage_map()

    with factory() as session:
        run = session.get(Run, run_id, options=[selectinload(Run.steps)])
        if not run:
            logger.error("run not found run_id=%s", run_id)
            return

        if run.status in (RunStatus.succeeded, RunStatus.cancelled):
            return

        run.status = RunStatus.running
        session.commit()

        registry = IntegrationRegistry.load(session)
        upstream_context: dict = {}

        try:
            for step in sorted(run.steps, key=lambda s: s.ordinal):
                if step.status in (StepStatus.succeeded, StepStatus.skipped):
                    continue

                st = smap.get(step.stage_key)
                if not st:
                    step.status = StepStatus.failed
                    step.error_message = "unknown_stage_key"
                    step.finished_at = datetime.now(timezone.utc)
                    run.status = RunStatus.failed
                    run.error_message = step.error_message
                    session.commit()
                    return

                if st.requires_human and not settings.require_human_approval:
                    step.status = StepStatus.skipped
                    step.skipped_reason = "human_gate_disabled_for_automation"
                    step.finished_at = datetime.now(timezone.utc)
                    session.commit()
                    continue

                if st.requires_human and settings.require_human_approval:
                    step.status = StepStatus.waiting_human
                    step.started_at = datetime.now(timezone.utc)
                    run.status = RunStatus.waiting_human
                    session.commit()
                    logger.info(
                        "run waiting for human approval run_id=%s step=%s",
                        run_id,
                        step.stage_key,
                    )
                    return

                skip_reason = skip_reason_for_stage(step.stage_key, run.output_mode, registry)
                if skip_reason:
                    step.status = StepStatus.skipped
                    step.skipped_reason = skip_reason
                    step.finished_at = datetime.now(timezone.utc)
                    step.detail = {**(step.detail or {}), "integration_skip": True}
                    session.commit()
                    logger.info(
                        "step skipped run_id=%s stage=%s reason=%s",
                        run_id,
                        step.stage_key,
                        skip_reason,
                    )
                    continue

                step.status = StepStatus.running
                step.started_at = datetime.now(timezone.utc)
                session.commit()

                with usage_scope() as usage_buf:
                    detail_patch, context_out = execute_stage(
                        step.stage_key,
                        run,
                        settings,
                        upstream_context,
                    )
                for u in usage_buf:
                    session.add(
                        ProviderUsage(
                            run_id=run.id,
                            run_step_id=step.id,
                            provider=u["provider"],
                            model=u.get("model"),
                            input_tokens=u.get("input_tokens"),
                            output_tokens=u.get("output_tokens"),
                            detail=None,
                        )
                    )
                upstream_context.update(context_out)
                step.status = StepStatus.succeeded
                step.finished_at = datetime.now(timezone.utc)
                step.detail = {**(step.detail or {}), **detail_patch}
                session.commit()
                logger.info("step ok run_id=%s stage=%s", run_id, step.stage_key)

            run.status = RunStatus.succeeded
            run.error_message = None
            session.commit()
            logger.info("run succeeded run_id=%s", run_id)

        except Exception as e:
            logger.exception("run failed run_id=%s", run_id)
            run = session.get(Run, run_id)
            if run:
                run.status = RunStatus.failed
                run.error_message = str(e)[:2000]
            active = session.execute(
                select(RunStep).where(
                    RunStep.run_id == run_id,
                    RunStep.status == StepStatus.running,
                )
            ).scalar_one_or_none()
            if active:
                active.status = StepStatus.failed
                active.error_message = str(e)[:2000]
                active.finished_at = datetime.now(timezone.utc)
            session.commit()
