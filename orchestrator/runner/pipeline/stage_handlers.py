"""
Per-stage execution: live integrations when env is configured, else short stub.

Returns (detail_patch, context_out) merged by the runner into step.detail and upstream context.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from runner.config import Settings
from runner.integrations import llm_simple, supabase_rest
from runner.models import Run

StageResult = tuple[dict[str, Any], dict[str, Any]]


def _stub() -> StageResult:
    time.sleep(0.05)
    return ({"stub": True}, {})


def _supabase_ready(s: Settings) -> bool:
    return bool(s.supabase_url and s.supabase_service_key)


def _llm_ready(s: Settings) -> bool:
    return bool(s.anthropic_api_key or s.openai_api_key)


def _ctx_dict(ctx: dict[str, Any], key: str) -> dict[str, Any]:
    v = ctx.get(key)
    return v if isinstance(v, dict) else {}


def _ctx_list(ctx: dict[str, Any], key: str) -> list | None:
    v = ctx.get(key)
    return v if isinstance(v, list) else None


def handle_ingest_config(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    live_supabase = _supabase_ready(s)
    live_llm = _llm_ready(s)
    mode = "live" if (live_supabase or live_llm) else "demo"
    detail = {
        "stub": not (live_supabase or live_llm),
        "pipeline_mode": mode,
        "capabilities": {
            "supabase_rest": live_supabase,
            "anthropic": bool(s.anthropic_api_key),
            "openai": bool(s.openai_api_key),
        },
        "run_meta_keys": sorted((run.meta or {}).keys()),
    }
    out = {"run_meta": run.meta or {}}
    return (detail, out)


def handle_build_daily_context(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _llm_ready(s):
        return _stub()
    meta = ctx.get("run_meta") or run.meta or {}
    if not isinstance(meta, dict):
        meta = {}
    provider, blob = llm_simple.run_build_daily_context_llm(
        anthropic_key=s.anthropic_api_key,
        anthropic_model=s.anthropic_model,
        openai_key=s.openai_api_key,
        openai_model=s.openai_model,
        run_meta=meta,
        output_mode=run.output_mode.value,
        max_tokens=s.planning_context_max_tokens,
    )
    return (
        {"stub": False, "llm_provider": provider, "daily_context": blob},
        {"daily_context": blob},
    )


def handle_merge_signal(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _llm_ready(s):
        return _stub()
    meta = ctx.get("run_meta") or run.meta or {}
    if not isinstance(meta, dict):
        meta = {}
    daily = _ctx_dict(ctx, "daily_context")
    provider, blob = llm_simple.run_merge_signal_llm(
        anthropic_key=s.anthropic_api_key,
        anthropic_model=s.anthropic_model,
        openai_key=s.openai_api_key,
        openai_model=s.openai_model,
        run_meta=meta,
        daily_context=daily,
        max_tokens=s.planning_context_max_tokens,
    )
    return (
        {"stub": False, "llm_provider": provider, "merged_signal": blob},
        {"merged_signal": blob},
    )


def handle_normalize_last_arc(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _supabase_ready(s):
        return _stub()
    cid = (run.meta or {}).get("character_id")
    if not cid or not isinstance(cid, str):
        return (
            {
                "stub": True,
                "skipped_live_fetch": True,
                "reason": "run.meta.character_id not set",
            },
            {},
        )
    row = supabase_rest.fetch_latest_character_episode(
        s.supabase_url or "",
        s.supabase_service_key or "",
        cid,
    )
    return (
        {"stub": False, "source": "supabase", "character_id": cid, "latest_episode": row},
        {"last_episode": row} if row else {},
    )


def handle_assemble_context_pack(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _supabase_ready(s):
        return _stub()
    rows = supabase_rest.fetch_editorial_calendar_preview(
        s.supabase_url or "",
        s.supabase_service_key or "",
        limit=s.supabase_editorial_limit,
    )
    return (
        {
            "stub": False,
            "source": "supabase",
            "editorial_row_count": len(rows),
            "editorial_calendar": rows,
        },
        {"editorial_calendar": rows},
    )


def handle_story_architect(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _llm_ready(s):
        return _stub()
    editorial = _ctx_list(ctx, "editorial_calendar")
    last_ep = ctx.get("last_episode")
    if last_ep is not None and not isinstance(last_ep, dict):
        last_ep = None
    daily = _ctx_dict(ctx, "daily_context")
    merged = _ctx_dict(ctx, "merged_signal")
    canon = ctx.get("character_canon")
    if canon is not None and not isinstance(canon, dict):
        canon = None
    provider, raw = llm_simple.run_story_architect_llm(
        anthropic_key=s.anthropic_api_key,
        anthropic_model=s.anthropic_model,
        openai_key=s.openai_api_key,
        openai_model=s.openai_model,
        editorial_rows=editorial,
        run_meta=ctx.get("run_meta") or run.meta or {},
        last_episode=last_ep,
        daily_context=daily or None,
        merged_signal=merged or None,
        character_canon=canon,
    )
    parsed = llm_simple.parse_story_architect_output(raw)
    detail: dict[str, Any] = {
        "stub": False,
        "llm_provider": provider,
        "story": parsed,
        "raw_preview": raw[:2000] if len(raw) > 2000 else raw,
    }
    if len(raw) > 2000:
        detail["raw_truncated"] = True
    return (detail, {"story_architect": parsed})


def handle_audience_framing(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _llm_ready(s):
        return _stub()
    story = _ctx_dict(ctx, "story_architect")
    editorial = _ctx_list(ctx, "editorial_calendar")
    daily = _ctx_dict(ctx, "daily_context")
    merged = _ctx_dict(ctx, "merged_signal")
    provider, blob = llm_simple.run_audience_framing_llm(
        anthropic_key=s.anthropic_api_key,
        anthropic_model=s.anthropic_model,
        openai_key=s.openai_api_key,
        openai_model=s.openai_model,
        story_architect=story,
        editorial_calendar=editorial,
        daily_context=daily,
        merged_signal=merged,
        max_tokens=s.planning_context_max_tokens,
    )
    return (
        {"stub": False, "llm_provider": provider, "audience_framing": blob},
        {"audience_framing": blob},
    )


def handle_signal_agent(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _llm_ready(s):
        return _stub()
    audience = _ctx_dict(ctx, "audience_framing")
    story = _ctx_dict(ctx, "story_architect")
    merged = _ctx_dict(ctx, "merged_signal")
    provider, blob = llm_simple.run_signal_agent_llm(
        anthropic_key=s.anthropic_api_key,
        anthropic_model=s.anthropic_model,
        openai_key=s.openai_api_key,
        openai_model=s.openai_model,
        audience_framing=audience,
        story_architect=story,
        merged_signal=merged,
        max_tokens=s.planning_context_max_tokens,
    )
    return (
        {"stub": False, "llm_provider": provider, "signal_agent": blob},
        {"signal_agent": blob},
    )


def handle_character_memory(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _supabase_ready(s):
        return _stub()
    cid = (run.meta or {}).get("character_id")
    if not cid or not isinstance(cid, str):
        return (
            {
                "stub": True,
                "skipped_live_fetch": True,
                "reason": "run.meta.character_id not set",
            },
            {},
        )
    row = supabase_rest.fetch_character_canon(
        s.supabase_url or "",
        s.supabase_service_key or "",
        cid,
    )
    return (
        {
            "stub": False,
            "source": "supabase",
            "character_id": cid,
            "character_canon": row,
        },
        {"character_canon": row} if row else {},
    )


def handle_research_agent(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _llm_ready(s):
        return _stub()
    story = ctx.get("story_architect")
    if story is not None and not isinstance(story, dict):
        story = {}
    if story is None:
        story = {}
    editorial = ctx.get("editorial_calendar")
    if editorial is not None and not isinstance(editorial, list):
        editorial = None
    last_ep = ctx.get("last_episode")
    if last_ep is not None and not isinstance(last_ep, dict):
        last_ep = None
    canon = ctx.get("character_canon")
    if canon is not None and not isinstance(canon, dict):
        canon = None

    provider, research, trace = llm_simple.run_research_pipeline(
        anthropic_key=s.anthropic_api_key,
        anthropic_model=s.anthropic_model,
        openai_key=s.openai_api_key,
        openai_model=s.openai_model,
        research_max_tokens=s.research_max_tokens,
        theology_review_max_tokens=s.theology_review_max_tokens,
        theology_max_revision_rounds=s.theology_max_revision_rounds,
        story_architect=story,
        editorial_calendar=editorial,
        last_episode=last_ep,
        character_memory=canon,
        run_meta=ctx.get("run_meta") or run.meta or {},
        daily_context=_ctx_dict(ctx, "daily_context"),
        merged_signal=_ctx_dict(ctx, "merged_signal"),
        audience_framing=_ctx_dict(ctx, "audience_framing"),
        signal_agent=_ctx_dict(ctx, "signal_agent"),
    )
    detail: dict[str, Any] = {
        "stub": False,
        "llm_provider": provider,
        "research": research,
        "theology_trace": trace,
    }
    return (detail, {"research": research})


def handle_scriptwriter(run: Run, s: Settings, ctx: dict[str, Any]) -> StageResult:
    if not _llm_ready(s):
        return _stub()
    story = ctx.get("story_architect")
    if not isinstance(story, dict):
        story = {}
    research = ctx.get("research")
    if not isinstance(research, dict):
        research = {}

    provider, script, trace = llm_simple.run_script_pipeline(
        anthropic_key=s.anthropic_api_key,
        anthropic_model=s.anthropic_model,
        openai_key=s.openai_api_key,
        openai_model=s.openai_model,
        script_max_tokens=s.script_max_tokens,
        script_guard_max_tokens=s.script_guard_max_tokens,
        script_guard_max_revision_rounds=s.script_guard_max_revision_rounds,
        story_architect=story,
        research=research,
        run_meta=ctx.get("run_meta") or run.meta or {},
        daily_context=_ctx_dict(ctx, "daily_context"),
        merged_signal=_ctx_dict(ctx, "merged_signal"),
        audience_framing=_ctx_dict(ctx, "audience_framing"),
        signal_agent=_ctx_dict(ctx, "signal_agent"),
    )
    detail = {
        "stub": False,
        "llm_provider": provider,
        "script": script,
        "guardrail_trace": trace,
    }
    return (detail, {"script": script})


HANDLERS: dict[str, Callable[[Run, Settings, dict[str, Any]], StageResult]] = {
    "ingest_config": handle_ingest_config,
    "build_daily_context": handle_build_daily_context,
    "merge_signal": handle_merge_signal,
    "normalize_last_arc": handle_normalize_last_arc,
    "assemble_context_pack": handle_assemble_context_pack,
    "character_memory": handle_character_memory,
    "story_architect": handle_story_architect,
    "audience_framing": handle_audience_framing,
    "signal_agent": handle_signal_agent,
    "research_agent": handle_research_agent,
    "scriptwriter": handle_scriptwriter,
}


def execute_stage(stage_key: str, run: Run, settings: Settings, upstream: dict[str, Any]) -> StageResult:
    fn = HANDLERS.get(stage_key)
    if fn:
        return fn(run, settings, upstream)
    return _stub()
