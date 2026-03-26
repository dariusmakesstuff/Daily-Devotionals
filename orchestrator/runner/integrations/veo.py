"""Google Vertex Veo — long-running predict + poll (stub behind integration flag)."""

from __future__ import annotations

from typing import Any


def start_veo_generation_stub(*, prompt: str, run_step_id: str) -> dict[str, Any]:
    """Replace with Vertex `predictLongRunning` + operation poll."""
    return {
        "status": "stub",
        "message": "Veo not configured — wire Vertex AI video generation here.",
        "prompt_preview": prompt[:200],
        "run_step_id": run_step_id,
    }


def poll_veo_operation_stub(operation_name: str) -> dict[str, Any]:
    return {"done": False, "operation_name": operation_name, "stub": True}
