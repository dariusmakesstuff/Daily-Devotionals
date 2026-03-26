"""Patch DV001 n8n workflow: align Scriptwriter + Guardrail parsers, fix Slack refs."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r"c:\Users\Darius Parlor\Downloads\DV001_Daily_Devotional_Orchestrator.json"

NEW_SCRIPT_SCHEMA = """Return ONLY valid JSON:
{
  "title": "3-6 words — a moment title from THIS story_brief, not a template",
  "hook": "First-person cold open — use story_brief.story_hook or equivalent; mid-thought, no greeting; must match THIS character and scene",
  "story_scenario": "One dense sentence: who (first name from story_brief.character_name only), where/when, tension, cost",
  "ghost_scene_descriptions": [
    "Visual 1 tied to THIS episode's concrete setting",
    "Visual 2",
    "Visual 3"
  ],
  "script_short": "120-170 words, first person as the host living the story — Walk With Me style; God/scripture discovered inside the story, not announced at the top",
  "script_extended": "200-280 words, same voice, more breathing room and complication before landing",
  "caption": "2-3 lines like a real person (not brand voice) + sparse relevant hashtags",
  "tagline": "Stay rooted. Stay ready."
}"""

NEW_GUARD_SCHEMA = """{
  "approved": true,
  "score": 8.5,
  "theology_status": "PASS",
  "craft_status": "PASS",
  "theology_issues": [],
  "craft_issues": [],
  "craft_warnings": [],
  "hard_blocks": [],
  "revision_notes": "",
  "approved_with_notes": false
}"""

with open(path, encoding="utf-8") as f:
    wf = json.load(f)

for n in wf["nodes"]:
    if n.get("name") == "✍️ Scriptwriter Agent":
        t = n["parameters"]["text"]
        marker = "Return ONLY valid JSON:"
        if marker not in t:
            raise SystemExit("Scriptwriter: marker not found")
        head = t[: t.index(marker)].rstrip() + "\n\n"
        head = head.replace(
            "Build the narrative architecture for today's Walk With Me episode.",
            "Build the script package for today's Walk With Me episode (JSON keys must match the structured output parser exactly).",
        )
        enc = (
            "Encode narrative architecture inside these keys: story_scenario = spine of the moment; "
            "script_short and script_extended = first-person HOST-voice story the Voice Writer turns into HOST + REFLECTION dialogue. "
            "The character's first name must be story_brief.character_name (or Character Memory continuation) — never a placeholder example name.\n\n"
        )
        if "Encode narrative architecture inside these keys" not in head:
            parts = head.split("\n\n", 1)
            if len(parts) == 2:
                head = parts[0] + "\n\n" + enc + parts[1]
            else:
                head = head + enc
        n["parameters"]["text"] = head + NEW_SCRIPT_SCHEMA

        sm = n["parameters"]["options"]["systemMessage"]
        sm = sm.replace(
            "Never default to a recurring placeholder name (e.g. Marcus) unless that exact name is in story_brief or canon for this run.",
            "Never default to a recurring placeholder name from examples or prior episodes unless that exact name is in story_brief or Character Memory for this run.",
        )
        sm = sm.replace(
            "Parser/schema examples in tooling are illustrative shapes only — your output must match today's brief, not yesterday's episode.",
            "The user message ends with the exact JSON schema you must output (title, hook, story_scenario, ghost_scene_descriptions, script_short, script_extended, caption, tagline) — match it character-for-character on keys.",
        )
        n["parameters"]["options"]["systemMessage"] = sm

    if n.get("name") == "🛡️ Theology Guardrail (Script)":
        gt = n["parameters"]["text"]
        if '"score"' not in gt.split("Return ONLY valid JSON:", 1)[-1]:
            gt = gt.replace(
                '{\n  "approved": true or false,\n  "theology_status"',
                '{\n  "approved": true or false,\n  "score": 1-10 number combining theology + craft confidence (10 = fully sound),\n  "theology_status"',
            )
            n["parameters"]["text"] = gt

    if n.get("name") == "Parser: Guardrail-2 Output":
        n["parameters"]["jsonSchemaExample"] = NEW_GUARD_SCHEMA

    if n.get("name") == "Build Slack Approval Message":
        code = n["parameters"]["jsCode"]
        code = code.replace(
            "Theology Score: ${guard.score}/10",
            "Theology Score: ${(guard.output && guard.output.score != null) ? guard.output.score : '—'}/10",
        )
        n["parameters"]["jsCode"] = code

    if n.get("name") == "🔔 Notify: Script Rejected":
        n["parameters"]["body"] = (
            "={\"text\":\"❌ *Devotional {{ $('Set Global Config').first().json.run_id }}*\\n"
            "Script FAILED standards review.\\nTheology: {{ $('🛡️ Theology Guardrail (Script)').first().json.output.theology_status }} "
            "Craft: {{ $('🛡️ Theology Guardrail (Script)').first().json.output.craft_status }}\\n"
            "Revision notes: {{ $('🛡️ Theology Guardrail (Script)').first().json.output.revision_notes }}\\n"
            "Issues: {{ JSON.stringify({ theology: $('🛡️ Theology Guardrail (Script)').first().json.output.theology_issues, "
            "craft: $('🛡️ Theology Guardrail (Script)').first().json.output.craft_issues, "
            "hard_blocks: $('🛡️ Theology Guardrail (Script)').first().json.output.hard_blocks }) }}\\n"
            "Action: revise per revision_notes.\"}"
        )

with open(path, "w", encoding="utf-8") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")

print("Patched:", path)
