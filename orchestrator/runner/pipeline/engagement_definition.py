"""DV080-aligned engagement stages (ingest → fetch → classify → persist)."""

from __future__ import annotations

from dataclasses import dataclass

from runner.models_extended import EngagementRunStep


@dataclass(frozen=True)
class EngagementStageDef:
    key: str
    title: str


ENGAGEMENT_STAGES: tuple[EngagementStageDef, ...] = (
    EngagementStageDef("eng_ingest", "Ingest engagement config"),
    EngagementStageDef("eng_fetch", "Fetch platform comments / signals"),
    EngagementStageDef("eng_classify", "Classify + story-safe scoring (LLM)"),
    EngagementStageDef("eng_persist", "Persist to Supabase / Sheets"),
)


def steps_for_engagement_run() -> list[EngagementRunStep]:
    return [
        EngagementRunStep(
            ordinal=i,
            stage_key=st.key,
            title=st.title,
            status="pending",
            detail={},
        )
        for i, st in enumerate(ENGAGEMENT_STAGES)
    ]
