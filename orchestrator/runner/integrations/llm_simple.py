from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from runner.integrations.llm_usage import record_llm_usage

logger = logging.getLogger(__name__)

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.I)


def _extract_json_text(raw: str) -> str:
    raw = raw.strip()
    m = _JSON_FENCE.search(raw)
    if m:
        return m.group(1).strip()
    return raw


def parse_json_object(raw: str) -> dict[str, Any]:
    """Best-effort parse of model output into a dict."""
    text = _extract_json_text(raw)
    try:
        out = json.loads(text)
        if isinstance(out, dict):
            return out
    except json.JSONDecodeError:
        pass
    return {"raw_text": raw[:8000], "parse_error": True}


def parse_story_architect_output(raw: str) -> dict[str, Any]:
    return parse_json_object(raw)


def anthropic_complete(api_key: str, model: str, system: str, user: str, max_tokens: int = 1024) -> str:
    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        record_llm_usage(
            provider="anthropic",
            model=model,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )
        blocks = data.get("content") or []
        if blocks and isinstance(blocks[0], dict) and blocks[0].get("text"):
            return str(blocks[0]["text"])
        return json.dumps(data)[:4000]


def openai_complete(api_key: str, model: str, system: str, user: str, max_tokens: int = 1024) -> str:
    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        record_llm_usage(
            provider="openai",
            model=model,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )
        choices = data.get("choices") or []
        if choices and choices[0].get("message", {}).get("content"):
            return str(choices[0]["message"]["content"])
        return json.dumps(data)[:4000]


def run_story_architect_llm(
    *,
    anthropic_key: str | None,
    anthropic_model: str,
    openai_key: str | None,
    openai_model: str,
    editorial_rows: list[dict[str, Any]] | None,
    run_meta: dict[str, Any],
    last_episode: dict[str, Any] | None,
    daily_context: dict[str, Any] | None = None,
    merged_signal: dict[str, Any] | None = None,
    character_canon: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Returns (provider_label, raw_model_text)."""
    system = (
        "You are a story architect for short Christian devotionals. "
        "Reply with a single JSON object only, no markdown outside JSON, keys: "
        "logline (string), beats (array of 3-5 short strings), tone (string)."
    )
    parts = [
        f"Run meta (JSON): {json.dumps(run_meta, default=str)[:6000]}",
    ]
    if daily_context:
        parts.append(f"Daily context: {json.dumps(daily_context, default=str)[:5000]}")
    if merged_signal:
        parts.append(f"Merged signal bundle: {json.dumps(merged_signal, default=str)[:5000]}")
    if character_canon:
        parts.append(f"Character canon: {json.dumps(character_canon, default=str)[:5000]}")
    if editorial_rows:
        parts.append(f"Recent editorial calendar rows: {json.dumps(editorial_rows, default=str)[:6000]}")
    if last_episode:
        parts.append(f"Latest character episode snapshot: {json.dumps(last_episode, default=str)[:6000]}")
    user = "\n\n".join(parts)

    if anthropic_key:
        text = anthropic_complete(anthropic_key, anthropic_model, system, user)
        return "anthropic", text
    if openai_key:
        text = openai_complete(openai_key, openai_model, system, user)
        return "openai", text
    raise RuntimeError("no_llm_key_configured")


def complete_llm(
    *,
    anthropic_key: str | None,
    anthropic_model: str,
    openai_key: str | None,
    openai_model: str,
    system: str,
    user: str,
    max_tokens: int = 2048,
) -> tuple[str, str]:
    if anthropic_key:
        return "anthropic", anthropic_complete(anthropic_key, anthropic_model, system, user, max_tokens)
    if openai_key:
        return "openai", openai_complete(openai_key, openai_model, system, user, max_tokens)
    raise RuntimeError("no_llm_key_configured")


def run_build_daily_context_llm(
    *,
    anthropic_key: str | None,
    anthropic_model: str,
    openai_key: str | None,
    openai_model: str,
    run_meta: dict[str, Any],
    output_mode: str,
    max_tokens: int,
) -> tuple[str, dict[str, Any]]:
    system = (
        "You set the day's creative posture for a Christian audio devotional pipeline. "
        "Output JSON only: day_posture (string), season_or_liturgical_note (string), "
        "creative_constraints (array of strings), prayed_intentions (array of short strings)."
    )
    user = json.dumps({"run_meta": run_meta, "output_mode": output_mode}, default=str)[:8000]
    provider, raw = complete_llm(
        anthropic_key=anthropic_key,
        anthropic_model=anthropic_model,
        openai_key=openai_key,
        openai_model=openai_model,
        system=system,
        user=user,
        max_tokens=max_tokens,
    )
    return provider, parse_json_object(raw)


def run_merge_signal_llm(
    *,
    anthropic_key: str | None,
    anthropic_model: str,
    openai_key: str | None,
    openai_model: str,
    run_meta: dict[str, Any],
    daily_context: dict[str, Any],
    max_tokens: int,
) -> tuple[str, dict[str, Any]]:
    system = (
        "Merge planning signals into one ranked bundle for downstream story and research agents. "
        "Output JSON only: merged_summary (string), priority_hooks (array of strings), "
        "risks_or_tensions (array of strings), noise_to_ignore (array of strings)."
    )
    user = json.dumps({"run_meta": run_meta, "daily_context": daily_context}, default=str)[:12000]
    provider, raw = complete_llm(
        anthropic_key=anthropic_key,
        anthropic_model=anthropic_model,
        openai_key=openai_key,
        openai_model=openai_model,
        system=system,
        user=user,
        max_tokens=max_tokens,
    )
    return provider, parse_json_object(raw)


def run_audience_framing_llm(
    *,
    anthropic_key: str | None,
    anthropic_model: str,
    openai_key: str | None,
    openai_model: str,
    story_architect: dict[str, Any],
    editorial_calendar: list[dict[str, Any]] | None,
    daily_context: dict[str, Any],
    merged_signal: dict[str, Any],
    max_tokens: int,
) -> tuple[str, dict[str, Any]]:
    system = (
        "You define audience framing for a short Christian audio devotional. "
        "Output JSON only: persona (string), pain_points (array of strings), "
        "hope_posture (string), listening_context (string: commute, morning, etc.)."
    )
    payload = {
        "story_architect": story_architect,
        "editorial_calendar": editorial_calendar or [],
        "daily_context": daily_context,
        "merged_signal": merged_signal,
    }
    user = f"Framing inputs (JSON):\n{json.dumps(payload, default=str)[:14000]}"
    provider, raw = complete_llm(
        anthropic_key=anthropic_key,
        anthropic_model=anthropic_model,
        openai_key=openai_key,
        openai_model=openai_model,
        system=system,
        user=user,
        max_tokens=max_tokens,
    )
    return provider, parse_json_object(raw)


def run_signal_agent_llm(
    *,
    anthropic_key: str | None,
    anthropic_model: str,
    openai_key: str | None,
    openai_model: str,
    audience_framing: dict[str, Any],
    story_architect: dict[str, Any],
    merged_signal: dict[str, Any],
    max_tokens: int,
) -> tuple[str, dict[str, Any]]:
    system = (
        "You propose signal hooks for social and discovery (not full posts). "
        "Output JSON only: trend_hooks (array of strings), platform_notes (object with "
        "optional keys youtube, instagram, tiktok each string), engagement_seeds (array of strings)."
    )
    payload = {
        "audience_framing": audience_framing,
        "story_architect": story_architect,
        "merged_signal": merged_signal,
    }
    user = f"Signal inputs (JSON):\n{json.dumps(payload, default=str)[:14000]}"
    provider, raw = complete_llm(
        anthropic_key=anthropic_key,
        anthropic_model=anthropic_model,
        openai_key=openai_key,
        openai_model=openai_model,
        system=system,
        user=user,
        max_tokens=max_tokens,
    )
    return provider, parse_json_object(raw)


def run_research_pipeline(
    *,
    anthropic_key: str | None,
    anthropic_model: str,
    openai_key: str | None,
    openai_model: str,
    research_max_tokens: int,
    theology_review_max_tokens: int,
    theology_max_revision_rounds: int,
    story_architect: dict[str, Any],
    editorial_calendar: list[dict[str, Any]] | None,
    last_episode: dict[str, Any] | None,
    character_memory: dict[str, Any] | None,
    run_meta: dict[str, Any],
    daily_context: dict[str, Any] | None = None,
    merged_signal: dict[str, Any] | None = None,
    audience_framing: dict[str, Any] | None = None,
    signal_agent: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    """
    Initial research pack + theology reviewer loop (review → revise up to N times).
    Returns (provider, final_research_dict, trace for step.detail).
    """
    trace: list[dict[str, Any]] = []
    ctx_blob: dict[str, Any] = {
        "run_meta": run_meta,
        "story_architect": story_architect,
        "editorial_calendar": editorial_calendar or [],
        "last_episode": last_episode,
        "character_canon": character_memory,
        "daily_context": daily_context or {},
        "merged_signal": merged_signal or {},
        "audience_framing": audience_framing or {},
        "signal_agent": signal_agent or {},
    }
    system_r = (
        "You are a research assistant for short Christian audio devotionals. "
        "Output a single JSON object only, keys: "
        "themes (array of strings), "
        "scripture_candidates (array of objects with ref, rationale), "
        "historical_notes (string), "
        "application_angles (array of strings), "
        "theology_self_check (object with status: ok|caution, notes: string)."
    )
    user_r = f"Context (JSON):\n{json.dumps(ctx_blob, default=str)[:14000]}"
    provider, raw = complete_llm(
        anthropic_key=anthropic_key,
        anthropic_model=anthropic_model,
        openai_key=openai_key,
        openai_model=openai_model,
        system=system_r,
        user=user_r,
        max_tokens=research_max_tokens,
    )
    research = parse_json_object(raw)
    trace.append({"step": "initial_research", "raw_preview": raw[:1800]})

    revision_round = 0
    while revision_round < theology_max_revision_rounds:
        system_rev = (
            "You are a conservative theology reviewer for evangelical devotional content. "
            "Output JSON only: approved (boolean), issues (array of objects with "
            "code, severity low|high, explanation). "
            "Approve true only if there are no substantive doctrinal problems."
        )
        user_rev = f"Research pack:\n{json.dumps(research, default=str)[:12000]}"
        _, raw_rev = complete_llm(
            anthropic_key=anthropic_key,
            anthropic_model=anthropic_model,
            openai_key=openai_key,
            openai_model=openai_model,
            system=system_rev,
            user=user_rev,
            max_tokens=theology_review_max_tokens,
        )
        review = parse_json_object(raw_rev)
        trace.append({"step": f"theology_review_{revision_round}", "review": review})
        if review.get("approved") is True:
            break
        issues = review.get("issues") if isinstance(review.get("issues"), list) else []
        if not issues:
            break
        system_fix = (
            "Revise the research pack to address the reviewer issues. "
            "Output JSON only with the same keys as before: "
            "themes, scripture_candidates, historical_notes, application_angles, theology_self_check."
        )
        user_fix = (
            f"Prior research:\n{json.dumps(research, default=str)[:10000]}\n"
            f"Issues:\n{json.dumps(issues, default=str)[:6000]}"
        )
        _, raw_fix = complete_llm(
            anthropic_key=anthropic_key,
            anthropic_model=anthropic_model,
            openai_key=openai_key,
            openai_model=openai_model,
            system=system_fix,
            user=user_fix,
            max_tokens=research_max_tokens,
        )
        research = parse_json_object(raw_fix)
        trace.append({"step": f"theology_revise_{revision_round}", "raw_preview": raw_fix[:1800]})
        revision_round += 1

    return provider, research, trace


def run_script_pipeline(
    *,
    anthropic_key: str | None,
    anthropic_model: str,
    openai_key: str | None,
    openai_model: str,
    script_max_tokens: int,
    script_guard_max_tokens: int,
    script_guard_max_revision_rounds: int,
    story_architect: dict[str, Any],
    research: dict[str, Any],
    run_meta: dict[str, Any],
    daily_context: dict[str, Any] | None = None,
    merged_signal: dict[str, Any] | None = None,
    audience_framing: dict[str, Any] | None = None,
    signal_agent: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    """Draft script + editor guardrail loop. Returns (provider, script dict, trace)."""
    trace: list[dict[str, Any]] = []
    payload: dict[str, Any] = {
        "run_meta": run_meta,
        "story_architect": story_architect,
        "research": research,
        "daily_context": daily_context or {},
        "merged_signal": merged_signal or {},
        "audience_framing": audience_framing or {},
        "signal_agent": signal_agent or {},
    }
    system_s = (
        "You are a scriptwriter for a single-speaker audio devotional (warm, clear, not preachy). "
        "Output JSON only: title (string), script_markdown (string; use ## for sections), "
        "cold_open (string), closing_prayer_hint (string), "
        "estimated_word_count (integer, target under 900 words spoken)."
    )
    user_s = f"Write from this JSON context:\n{json.dumps(payload, default=str)[:16000]}"
    provider, raw = complete_llm(
        anthropic_key=anthropic_key,
        anthropic_model=anthropic_model,
        openai_key=openai_key,
        openai_model=openai_model,
        system=system_s,
        user=user_s,
        max_tokens=script_max_tokens,
    )
    script = parse_json_object(raw)
    trace.append({"step": "initial_script", "raw_preview": raw[:1800]})

    for round_idx in range(script_guard_max_revision_rounds):
        system_g = (
            "You are an editor guardrail for Christian devotional audio. "
            "Check theology, tone, clarity, and length. "
            "Output JSON only: approved (boolean), issues (array of short strings)."
        )
        user_g = f"Script JSON:\n{json.dumps(script, default=str)[:14000]}"
        _, raw_g = complete_llm(
            anthropic_key=anthropic_key,
            anthropic_model=anthropic_model,
            openai_key=openai_key,
            openai_model=openai_model,
            system=system_g,
            user=user_g,
            max_tokens=script_guard_max_tokens,
        )
        guard = parse_json_object(raw_g)
        trace.append({"step": f"script_guard_{round_idx}", "guard": guard})
        if guard.get("approved") is True:
            break
        issues = guard.get("issues")
        if not isinstance(issues, list) or not issues:
            break
        system_rs = (
            "Revise the devotional script JSON to fix every listed issue. "
            "Keep keys: title, script_markdown, cold_open, closing_prayer_hint, estimated_word_count. "
            "Output JSON only."
        )
        user_rs = (
            f"Current script:\n{json.dumps(script, default=str)[:12000]}\n"
            f"Issues:\n{json.dumps(issues, default=str)[:4000]}"
        )
        _, raw_rs = complete_llm(
            anthropic_key=anthropic_key,
            anthropic_model=anthropic_model,
            openai_key=openai_key,
            openai_model=openai_model,
            system=system_rs,
            user=user_rs,
            max_tokens=script_max_tokens,
        )
        script = parse_json_object(raw_rs)
        trace.append({"step": f"script_revise_{round_idx}", "raw_preview": raw_rs[:1800]})

    return provider, script, trace
