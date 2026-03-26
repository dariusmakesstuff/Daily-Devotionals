"""Synchronous engagement pipeline (DV080 port target)."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import selectinload

from runner.db import get_session_factory
from runner.integrations.registry import IntegrationRegistry
from runner.models_extended import EngagementRun

logger = logging.getLogger(__name__)


def execute_engagement_sync(run_id: uuid.UUID) -> None:
    factory = get_session_factory()
    with factory() as session:
        run = session.get(EngagementRun, run_id, options=[selectinload(EngagementRun.steps)])
        if not run:
            logger.error("engagement run not found id=%s", run_id)
            return
        if run.status in ("succeeded", "cancelled"):
            return

        run.status = "running"
        session.commit()
        registry = IntegrationRegistry.load(session)

        try:
            for step in sorted(run.steps, key=lambda s: s.ordinal):
                if step.status in ("succeeded", "skipped"):
                    continue
                if not registry.enabled("engagement"):
                    step.status = "skipped"
                    step.skipped_reason = "integration_disabled:engagement"
                    step.finished_at = datetime.now(timezone.utc)
                    session.commit()
                    continue

                step.status = "running"
                step.started_at = datetime.now(timezone.utc)
                session.commit()

                time.sleep(0.05)
                step.status = "succeeded"
                step.finished_at = datetime.now(timezone.utc)
                step.detail = {
                    **(step.detail or {}),
                    "stub": True,
                    "stage": step.stage_key,
                }
                session.commit()
                logger.info("engagement step ok run_id=%s stage=%s", run_id, step.stage_key)

            run.status = "succeeded"
            run.error_message = None
            session.commit()
        except Exception as e:
            logger.exception("engagement run failed id=%s", run_id)
            run = session.get(EngagementRun, run_id)
            if run:
                run.status = "failed"
                run.error_message = str(e)[:2000]
            session.commit()
