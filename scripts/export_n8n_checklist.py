"""Emit markdown checklist from DV001/DV080 n8n exports (run from repo root)."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "orchestrator" / "docs" / "N8N_STEP_CHECKLIST.md"
SOURCES = [
    (REPO / ".vscode" / "DV001_Daily_Devotional_Orchestrator (2).json", "DV001 Daily Devotional Orchestrator"),
    (REPO / ".vscode" / "DV080_Social_Engagement_Orchestrator.json", "DV080 Social Engagement Orchestrator"),
]

SKIP_SUBSTR = ("stickyNote", "errorTrigger")


def integration_hint(node_type: str) -> str:
    if "langchain" in node_type and "agent" in node_type:
        return "LLM agent"
    if "lmChat" in node_type:
        return "LLM chat model"
    if "httpRequest" in node_type:
        return "HTTP (Supabase, APIs)"
    if "googleSheets" in node_type:
        return "Google Sheets"
    if "youTube" in node_type:
        return "YouTube"
    if "uploadPost" in node_type or "blotato" in node_type:
        return "Upload Post / social publish"
    if "webhook" in node_type:
        return "Webhook trigger"
    if "scheduleTrigger" in node_type:
        return "Cron schedule"
    if "wait" in node_type:
        return "Wait / poll"
    if "if" in node_type:
        return "Branch"
    if "merge" in node_type:
        return "Merge"
    if "code" in node_type:
        return "Code transform"
    if "set" in node_type:
        return "Set fields"
    return "—"


def idempotency_note(node_type: str) -> str:
    if "webhook" in node_type or "scheduleTrigger" in node_type:
        return "Trigger: dedupe via idempotency_key on run create"
    if "httpRequest" in node_type:
        return "Use If-None-Match / idempotent POST where API supports"
    if "wait" in node_type:
        return "Persist poll token on run_step.detail; resume safe"
    if "uploadPost" in node_type or "youTube" in node_type:
        return "Publish: dedupe by platform + content hash"
    return "Stateless or re-entrant if inputs frozen in run snapshot"


def main() -> None:
    lines: list[str] = [
        "# n8n → orchestrator step checklist",
        "",
        "Parsed from exported workflows in `.vscode/`. Maps each actionable node to a **target service module**, "
        "**integration deps**, and **idempotency** notes for the custom runner.",
        "",
    ]
    for path, title in SOURCES:
        if not path.exists():
            lines.append(f"## {title}\n\n_MISSING: {path}_\n")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        nodes = data.get("nodes") or []
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| # | Node name | n8n type | Target module (orchestrator) | Integration | Idempotency |")
        lines.append("|---|-----------|----------|------------------------------|-------------|-------------|")
        i = 0
        for n in sorted(nodes, key=lambda x: (x.get("position", [0, 0])[1], x.get("position", [0, 0])[0])):
            t = n.get("type") or ""
            if any(s in t for s in SKIP_SUBSTR):
                continue
            i += 1
            name = (n.get("name") or "?").replace("|", "\\|")
            mod = "TBD map in `runner/pipeline/stage_handlers.py` + integrations"
            if "langchain.agent" in t:
                mod = "`llm_provider` + stage prompt"
            elif "httpRequest" in t:
                mod = "`integrations/*` REST client"
            elif "youTube" in t or "uploadPost" in t or "blotato" in t:
                mod = "`publish/*` behind registry"
            elif "wait" in t:
                mod = "`runner/pipeline/runner.py` long-step + detail poll state"
            elif "scheduleTrigger" in t or "webhook" in t:
                mod = "API trigger / external scheduler → `POST /runs`"
            lines.append(
                f"| {i} | {name} | `{t.split('.')[-1][:40]}` | {mod} | {integration_hint(t)} | {idempotency_note(t)} |"
            )
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
