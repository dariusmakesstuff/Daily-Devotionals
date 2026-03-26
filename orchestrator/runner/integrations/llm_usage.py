"""Per-step LLM usage capture via contextvars (flushed to `provider_usage` in runner)."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

_buffer: ContextVar[list[dict[str, Any]] | None] = ContextVar("llm_usage_buffer", default=None)


@contextmanager
def usage_scope() -> Iterator[list[dict[str, Any]]]:
    buf: list[dict[str, Any]] = []
    token = _buffer.set(buf)
    try:
        yield buf
    finally:
        _buffer.reset(token)


def record_llm_usage(
    *,
    provider: str,
    model: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    b = _buffer.get()
    if b is None:
        return
    b.append(
        {
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
    )
