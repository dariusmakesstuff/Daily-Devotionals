import asyncio
import uuid

from arq.connections import RedisSettings

from runner.config import get_settings
from runner.pipeline.engagement_runner import execute_engagement_sync
from runner.pipeline.runner import execute_run_sync


async def process_run(ctx, run_id: str) -> None:
    await asyncio.to_thread(execute_run_sync, uuid.UUID(run_id))


async def process_engagement_run(ctx, engagement_run_id: str) -> None:
    await asyncio.to_thread(execute_engagement_sync, uuid.UUID(engagement_run_id))


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    functions = [process_run, process_engagement_run]
