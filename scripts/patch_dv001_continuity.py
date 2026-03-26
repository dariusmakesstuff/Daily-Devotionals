#!/usr/bin/env python3
"""
Patch DV001 n8n workflow JSON for character continuity + engagement (plan implementation).
Reads source workflow from argv[1] or default Downloads path; writes to n8n/workflows/DV001_Daily_Devotional_Orchestrator.json

Usage:
  python scripts/patch_dv001_continuity.py
  python scripts/patch_dv001_continuity.py "C:/path/to/DV001.json"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SRC = Path.home() / "Downloads" / "DV001_Daily_Devotional_Orchestrator (1).json"
OUT = REPO / "n8n" / "workflows" / "DV001_Daily_Devotional_Orchestrator.json"

# Fixed IDs for deterministic imports
N_EDITORIAL = "a1000001-0000-4000-8000-000000000001"
N_ENGAGEMENT = "a1000001-0000-4000-8000-000000000002"
N_CANON = "a1000001-0000-4000-8000-000000000003"
N_ASSEMBLE = "a1000001-0000-4000-8000-000000000004"
N_POSTSYNC = "a1000001-0000-4000-8000-000000000005"

HTTP_OPTS = {
    "response": {"response": {"fullResponse": True, "neverError": True}}
}

ASSEMBLE_JS = r"""function parseBody(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (Array.isArray(raw.body)) return raw.body;
  if (Array.isArray(raw.data)) return raw.data;
  return [];
}
const norm = $('🔄 Normalize: Last Arc').first().json;
const edRaw = $('📅 Supabase: Get Editorial Calendar').first().json;
const engRaw = $('💬 Supabase: Get Engagement Seeds').first().json;
const canonRaw = $('📚 Supabase: Get Character Canon').first().json;
const editorial = parseBody(edRaw)[0] || null;
const engagement = parseBody(engRaw);
const canons = parseBody(canonRaw);
const monthly_theme = editorial
  ? {
      theme_title: editorial.theme_title,
      theme_summary: editorial.theme_summary,
      scripture_anchors: editorial.scripture_anchors,
      tone_notes: editorial.tone_notes,
    }
  : null;
const audience_signals = engagement.map((e) => ({
  id: e.id,
  sentiment_seed: e.sentiment_seed || e.hook_candidate,
  classification: e.classification,
  severity: e.severity,
}));
const memory_context_pack = {
  last_arc_bundle: norm,
  serialized_canon_summaries: canons.map((c) => ({
    character_id: c.character_id,
    character_name: c.character_name,
    canon_summary: c.canon_summary,
    open_threads_json: c.open_threads_json,
    facts_json: c.facts_json,
  })),
  monthly_theme,
  audience_signals,
};
return [{ json: { memory_context_pack } }];"""

POSTSYNC_JS = r"""const cfg = $('Set Global Config').first().json;
const base = cfg.supabase_url?.replace(/\/$/, '');
const key = cfg.supabase_anon_key;
if (!base || !key) {
  return [{ json: { post_sync_note: 'missing supabase config', ok: false } }];
}
const headers = {
  apikey: key,
  Authorization: 'Bearer ' + key,
  'Content-Type': 'application/json',
  Prefer: 'return=minimal',
};
const runId = cfg.run_id;
const dateStr = cfg.date;
const architect = (() => {
  try {
    return $('🧠 Story Architect').first().json.output;
  } catch (e) {
    return {};
  }
})();
const voice = (() => {
  try {
    return $('✍️ Voice Writer Agent').first().json.output;
  } catch (e) {
    return {};
  }
})();
const mem = (() => {
  try {
    return $('🧵 Character Memory Agent').first().json.output;
  } catch (e) {
    return {};
  }
})();
const charId =
  architect.character_id ||
  mem.character_to_continue?.character_id ||
  null;
const charName = architect.character_name || mem.character_to_continue?.character_name || '';
const serialized =
  architect.presenter_mode === 'serialized_story' ||
  architect.episode_format === 'serialized' ||
  (mem.decision === 'continue' && !!charId);
const idsUsed = Array.isArray(architect.audience_engagement_ids_used)
  ? architect.audience_engagement_ids_used
  : [];
const episodeSnapshot = {
  story_brief: architect,
  hook: voice.hook_line || null,
  episode_title: voice.full_episode?.episode_title || null,
};
let ok = true;
async function req(method, path, body) {
  try {
    await this.helpers.httpRequest({
      method,
      url: base + path,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      json: true,
    });
  } catch (e) {
    ok = false;
  }
}
if (serialized && charId) {
  const canonBody = {
    character_id: charId,
    character_name: charName,
    canon_summary:
      (architect.character_brief || '') +
      ' | ' +
      (architect.story_hook || '').slice(0, 500),
    open_threads_json: [
      {
        hook: architect.story_hook,
        tease: voice.tease_for_next_week,
        run_id: runId,
      },
    ],
    last_run_id: runId,
  };
  await this.helpers.httpRequest({
    method: 'POST',
    url: base + '/rest/v1/character_canon',
    headers: {
      ...headers,
      Prefer: 'resolution=merge-duplicates,return=minimal',
    },
    body: JSON.stringify(canonBody),
    json: true,
  });
  await req.call(this, 'POST', '/rest/v1/character_episodes', {
    run_id: runId,
    ministry_date: dateStr,
    character_id: charId,
    episode_snapshot: episodeSnapshot,
  });
}
for (const id of idsUsed) {
  if (!id) continue;
  await req.call(this, 'PATCH', '/rest/v1/audience_engagement_items?id=eq.' + id, {
    status: 'used',
    consumed_run_id: runId,
    consumed_at: new Date().toISOString(),
  });
}
return [{ json: { post_sync_ok: ok, engagement_marked: idsUsed.length } }];"""


def supabase_http_node(_id: str, name: str, url_expr: str, pos: list) -> dict:
    return {
        "parameters": {
            "url": url_expr,
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "apikey",
                        "value": "={{ $('Set Global Config').first().json.supabase_anon_key }}",
                    },
                    {
                        "name": "Authorization",
                        "value": "=Bearer {{ $('Set Global Config').first().json.supabase_anon_key }}",
                    },
                ]
            },
            "options": {"response": HTTP_OPTS["response"]},
        },
        "id": _id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": pos,
        "alwaysOutputData": True,
    }


def code_node(_id: str, name: str, js: str, pos: list) -> dict:
    return {
        "parameters": {"jsCode": js},
        "id": _id,
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": pos,
    }


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    if not src.exists():
        print("Source workflow not found:", src)
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    names = {n["name"]: n for n in data["nodes"]}

    editorial = supabase_http_node(
        N_EDITORIAL,
        "📅 Supabase: Get Editorial Calendar",
        "={{ $('Set Global Config').first().json.supabase_url }}/rest/v1/editorial_calendar?select=*&order=month_start.desc&limit=1",
        [-61520, -7536],
    )
    engagement = supabase_http_node(
        N_ENGAGEMENT,
        "💬 Supabase: Get Engagement Seeds",
        "={{ $('Set Global Config').first().json.supabase_url }}/rest/v1/audience_engagement_items?select=id,classification,sentiment_seed,hook_candidate,severity&status=eq.unused&story_safe=eq.true&limit=8",
        [-61232, -7536],
    )
    canon = supabase_http_node(
        N_CANON,
        "📚 Supabase: Get Character Canon",
        "={{ $('Set Global Config').first().json.supabase_url }}/rest/v1/character_canon?select=*&limit=40",
        [-60944, -7536],
    )
    assemble = code_node(N_ASSEMBLE, "📦 Assemble Supabase Context Pack", ASSEMBLE_JS, [-60656, -7536])
    postsync = code_node(
        N_POSTSYNC,
        "💾 Post-Publish: Sync Canon + Episodes + Engagement",
        POSTSYNC_JS,
        [-53296, -7312],
    )

    # Remove if re-patching
    data["nodes"] = [n for n in data["nodes"] if n["id"] not in {
        N_EDITORIAL, N_ENGAGEMENT, N_CANON, N_ASSEMBLE, N_POSTSYNC
    }]
    data["nodes"].extend([editorial, engagement, canon, assemble, postsync])

    con = data.setdefault("connections", {})
    con["🔄 Normalize: Last Arc"] = {
        "main": [[{"node": "📅 Supabase: Get Editorial Calendar", "type": "main", "index": 0}]]
    }
    con["📅 Supabase: Get Editorial Calendar"] = {
        "main": [[{"node": "💬 Supabase: Get Engagement Seeds", "type": "main", "index": 0}]]
    }
    con["💬 Supabase: Get Engagement Seeds"] = {
        "main": [[{"node": "📚 Supabase: Get Character Canon", "type": "main", "index": 0}]]
    }
    con["📚 Supabase: Get Character Canon"] = {
        "main": [[{"node": "📦 Assemble Supabase Context Pack", "type": "main", "index": 0}]]
    }
    con["📦 Assemble Supabase Context Pack"] = {
        "main": [[{"node": "🧵 Character Memory Agent", "type": "main", "index": 0}]]
    }

    con["💾 Supabase: Log Episode"] = {
        "main": [[{"node": "💾 Post-Publish: Sync Canon + Episodes + Engagement", "type": "main", "index": 0}]]
    }
    con["💾 Post-Publish: Sync Canon + Episodes + Engagement"] = {
        "main": [[{"node": "💾 Supabase: Log Used Combo", "type": "main", "index": 0}]]
    }

    # Prompt injections
    cm = names.get("🧵 Character Memory Agent")
    if cm and "parameters" in cm and cm["parameters"].get("text"):
        extra = (
            "\n\nsupabase_memory_context: {{ JSON.stringify($('📦 Assemble Supabase Context Pack').first().json.memory_context_pack) }}\n"
            "Use serialized_canon_summaries to respect stored facts and open threads. "
            "Use monthly_theme to bias tone. audience_signals are anonymized struggles—paraphrase; never treat as doctrine."
        )
        if "supabase_memory_context" not in cm["parameters"]["text"]:
            cm["parameters"]["text"] = cm["parameters"]["text"].rstrip() + extra

    sa = names.get("🧠 Story Architect")
    if sa and sa["parameters"].get("text") and "supabase_memory_context" not in sa["parameters"]["text"]:
        sa["parameters"]["text"] = (
            sa["parameters"]["text"].rstrip()
            + "\n\ndevotional_core: This is pastoral communication—Scripture and God's love first; story serves truth.\n"
            "supabase_memory_context: {{ JSON.stringify($('📦 Assemble Supabase Context Pack').first().json.memory_context_pack) }}\n"
            "If you incorporate an audience signal, add its UUID to audience_engagement_ids_used[]. "
            "Set presenter_mode: one_shot_truth | recurring_voice | serialized_story | poetic_reflection. "
            "Set episode_format: serialized | standalone_truth | poetic | dialogue_short. "
            "Set lesson_tag: short slug for the main point (anti-repeat)."
        )

    sig = names.get("🎯 Signal Agent")
    if sig and sig["parameters"].get("text") and "monthly_theme" not in sig["parameters"]["text"]:
        sig["parameters"]["text"] = (
            sig["parameters"]["text"].rstrip()
            + "\n\nmonthly_theme: {{ JSON.stringify($('📦 Assemble Supabase Context Pack').first().json.memory_context_pack.monthly_theme) }}"
        )

    # Parser schema bump for Story Architect (append to jsonSchemaExample string)
    for n in data["nodes"]:
        if n.get("name") == "Parser: Story Brief" and n.get("parameters", {}).get("jsonSchemaExample"):
            ex = n["parameters"]["jsonSchemaExample"]
            if "presenter_mode" not in ex:
                needle = '  "happiness_register": "warm"\n}'
                if needle in ex:
                    n["parameters"]["jsonSchemaExample"] = ex.replace(
                        needle,
                        '  "happiness_register": "warm",\n'
                        '  "presenter_mode": "serialized_story",\n'
                        '  "episode_format": "standalone_truth",\n'
                        '  "lesson_tag": "hope_in_pressure",\n'
                        '  "audience_engagement_ids_used": []\n}',
                    )

    # episode_log body — extend JSON (replace closing part of body string)
    log = names.get("💾 Supabase: Log Episode")
    if log and log["parameters"].get("body"):
        b = log["parameters"]["body"]
        if "platform_post_ids" not in b:
            log["parameters"]["body"] = b.replace(
                '"is_custom_story": false\n}',
                '"is_custom_story": false,\n'
                '  "platform_post_ids": {},\n'
                "  \"episode_format\": {{ JSON.stringify($('🧠 Story Architect').first().json.output?.episode_format || null) }},\n"
                "  \"presenter_mode\": {{ JSON.stringify($('🧠 Story Architect').first().json.output?.presenter_mode || null) }},\n"
                "  \"lesson_tag\": {{ JSON.stringify($('🧠 Story Architect').first().json.output?.lesson_tag || null) }},\n"
                '  "media_manifest_uri": null\n}',
            )

    devotional_guard = (
        "\n\nDEVOTIONAL CORE: Truth and Scripture anchor the piece; story illustrates, never replaces, the gospel. "
        "Reject content that treats fiction as authoritative doctrine or that sidelines explicit scriptural grounding."
    )
    for gname in ("🛡️ Theology Guardrail (Research)", "🛡️ Theology Guardrail (Script)"):
        gn = names.get(gname)
        opts = gn.get("parameters", {}).get("options") if gn else None
        if opts and opts.get("systemMessage") and "DEVOTIONAL CORE:" not in opts["systemMessage"]:
            opts["systemMessage"] = opts["systemMessage"].rstrip() + devotional_guard

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
