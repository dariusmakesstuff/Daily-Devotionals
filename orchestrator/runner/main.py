import logging
from contextlib import asynccontextmanager
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse

from runner.api.engagement import router as engagement_router
from runner.api.health import router as health_router
from runner.api.hooks import router as hooks_router
from runner.api.integrations import router as integrations_router
from runner.api.runs import router as runs_router
from runner.api.secrets_api import router as secrets_router
from runner.config import get_settings
from runner.db import init_db
from runner.middleware.request_context import RequestContextMiddleware

logging.basicConfig(level=get_settings().log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    if settings.sync_worker:
        app.state.arq_pool = None
        logger.info("sync_worker=true: runs execute in-process (no Redis/Arq)")
    else:
        app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        logger.info("Arq pool created for %s", settings.redis_url)
    try:
        yield
    finally:
        if app.state.arq_pool is not None:
            await app.state.arq_pool.close()
            logger.info("Arq pool closed")


app = FastAPI(
    title="Walk With Me Orchestrator",
    description="Phase 1 scaffold: durable run + step progress; swap stubs for real agents.",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(runs_router)
app.include_router(integrations_router)
app.include_router(secrets_router)
app.include_router(hooks_router)
app.include_router(engagement_router)


_DASHBOARD = Path(__file__).resolve().parent / "static" / "dashboard.html"


@app.get("/")
def root() -> RedirectResponse:
    """Landing page -> small management UI (not a full product frontend yet)."""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard")
def dashboard() -> FileResponse:
    """Minimal HTML UI: list runs, start runs, links to /docs and OpenAPI."""
    return FileResponse(_DASHBOARD, media_type="text/html")


def run() -> None:
    import uvicorn

    s = get_settings()
    uvicorn.run(
        "runner.main:app",
        host=s.api_host,
        port=s.api_port,
        reload=False,
    )


if __name__ == "__main__":
    run()
