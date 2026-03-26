"""Map stages → integration keys; return skip reason when integration is off."""

from __future__ import annotations

from runner.integrations.registry import IntegrationRegistry
from runner.models import OutputMode

# Stage → integration id required for "live" work; when off → skipped with explicit reason.
STAGE_INTEGRATION: dict[str, str] = {
    "tts_render": "tts",
    "veo_generate": "veo",
    "visual_director": "veo",
    "assemble_media": "media_assembly",
    "publish": "publish",
    "post_publish_sync": "supabase",
}


def skip_reason_for_stage(
    stage_key: str,
    output_mode: OutputMode,
    registry: IntegrationRegistry,
) -> str | None:
    if stage_key in ("veo_generate", "visual_director"):
        if output_mode != OutputMode.video:
            return None
    integ = STAGE_INTEGRATION.get(stage_key)
    if not integ:
        return None
    if registry.enabled(integ):
        return None
    return f"integration_disabled:{integ}"
