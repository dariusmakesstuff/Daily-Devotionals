from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from runner.config import get_settings

logger = logging.getLogger(__name__)
_ip_hits: dict[str, deque[float]] = defaultdict(deque)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach correlation id, basic rate limit, structured access log."""

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        cid = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = cid

        if settings.rate_limit_per_minute > 0:
            client = request.client.host if request.client else "unknown"
            now = time.time()
            window = 60.0
            dq = _ip_hits[client]
            while dq and now - dq[0] > window:
                dq.popleft()
            if len(dq) >= settings.rate_limit_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "rate limit exceeded"},
                    headers={"X-Correlation-ID": cid},
                )
            dq.append(now)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        logger.info(
            "%s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={"correlation_id": cid},
        )
        return response
