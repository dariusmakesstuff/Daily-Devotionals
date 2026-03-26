"""
Ordered pipeline stages (DV001-aligned). Stub execution today; swap in real agents per stage later.

Layout goals:
- Linear phases with clear dependencies (easier to test than a huge n8n graph).
- Human gate is optional and OFF by default for unattended runs.
- video_only stages are skipped (with reason) when output_mode is audio_only.
"""

from __future__ import annotations

from dataclasses import dataclass

from runner.models import OutputMode, RunStep, StepStatus


@dataclass(frozen=True)
class StageDef:
    key: str
    title: str
    requires_human: bool = False
    video_only: bool = False
    phase: str = "core"


# Order matches the intended devotional pipeline (see docs/AGENT_PIPELINE.md).
STAGES: tuple[StageDef, ...] = (
    StageDef("ingest_config", "Load run configuration", phase="setup"),
    StageDef("build_daily_context", "Build daily context", phase="context"),
    StageDef("merge_signal", "Merge signal sources", phase="context"),
    StageDef("normalize_last_arc", "Normalize last arc (continuity)", phase="memory"),
    StageDef("assemble_context_pack", "Assemble Supabase context pack", phase="memory"),
    StageDef("character_memory", "Character memory agent", phase="memory"),
    StageDef("story_architect", "Story architect", phase="planning"),
    StageDef("audience_framing", "Audience framing", phase="planning"),
    StageDef("signal_agent", "Signal agent", phase="planning"),
    StageDef("research_agent", "Research agent (+ theology loop)", phase="research"),
    StageDef("scriptwriter", "Scriptwriter (+ script guardrail loop)", phase="script"),
    StageDef(
        "human_approval_script",
        "Human approval (script)",
        requires_human=True,
        phase="gate",
    ),
    StageDef("visual_director", "Visual director", video_only=True, phase="video"),
    StageDef("veo_generate", "Vertex Veo generate + poll", video_only=True, phase="video"),
    StageDef("voice_writer", "Voice writer", phase="audio"),
    StageDef("tts_render", "TTS (multi-provider)", phase="audio"),
    StageDef("assemble_media", "Assemble (ffmpeg / Shotstack)", phase="media"),
    StageDef("publish", "Publish (YouTube, IG, FB, TikTok, …)", phase="publish"),
    StageDef("post_publish_sync", "Post-publish sync (Supabase, canon, engagement)", phase="finalize"),
)


def steps_for_new_run(output_mode: OutputMode) -> list[RunStep]:
    """Build persisted step rows for a new run (some may start as skipped)."""
    rows: list[RunStep] = []
    for i, st in enumerate(STAGES):
        if st.video_only and output_mode == OutputMode.audio_only:
            rows.append(
                RunStep(
                    ordinal=i,
                    stage_key=st.key,
                    title=st.title,
                    status=StepStatus.skipped,
                    skipped_reason="output_mode_is_audio_only",
                    detail={"phase": st.phase},
                )
            )
            continue
        rows.append(
            RunStep(
                ordinal=i,
                stage_key=st.key,
                title=st.title,
                status=StepStatus.pending,
                detail={"phase": st.phase, "requires_human": st.requires_human},
            )
        )
    return rows
