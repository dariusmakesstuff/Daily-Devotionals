# Agent pipeline layout (orchestrator)

This document is the **intended** order of work for the Walk With Me daily devotional runner. The n8n graph (DV001) is the behavioral spec; this layout reduces cross-wires and makes **unattended** runs the default.

## Principles

1. **Linear phases** — each phase completes before the next, except where noted (internal LLM loops stay inside one stage).
2. **Human gate optional** — `REQUIRE_HUMAN_APPROVAL=false` skips the script-approval wait (Slack parity) so production can run lights-out.
3. **Video is a branch** — `output_mode=audio_only` skips video-only stages; they appear as `skipped` with reason `output_mode_is_audio_only`.
4. **Integration toggles (future)** — each external system (Veo, Upload Post, TikTok, etc.) will register as optional; disabled integrations skip without failing the run when the stage is not required.

## Phase order

| Phase | Stage keys (high level) | Notes |
|-------|-------------------------|--------|
| setup | `ingest_config` | Load run + tenant config; correlation id. |
| context | `build_daily_context`, `merge_signal` | Day posture, YouVersion, trends — can parallelize later inside one activity. |
| memory | `normalize_last_arc`, `assemble_context_pack`, `character_memory` | Supabase continuity; feeds Story Architect. |
| planning | `story_architect`, `audience_framing`, `signal_agent` | Framing + signal after architect so prompts see story spine. |
| research | `research_agent` | Includes **theology guardrail loop** (max N) inside this stage in code. |
| script | `scriptwriter` | Includes **script guardrail loop** inside this stage. |
| gate | `human_approval_script` | **Skipped** when `REQUIRE_HUMAN_APPROVAL=false`. When true, run pauses in `waiting_human` until `POST /runs/{id}/resume`. |
| video | `visual_director`, `veo_generate` | **video** output only; Veo long-running + poll. |
| audio | `voice_writer`, `tts_render` | Multi-provider TTS. |
| media | `assemble_media` | ffmpeg and/or Shotstack; audio-only still muxes bed + voice. |
| publish | `publish` | YouTube, Instagram, Facebook, TikTok, Upload Post — each behind flags later. |
| finalize | `post_publish_sync` | Supabase episode log, canon, engagement markers. |

## Compared to n8n

- **Merges and routers** become **explicit branches** in code or workflow definition, not invisible edges.
- **Wait nodes** (Shotstack, Veo) stay **inside** the stage that owns them so retries are scoped.
- **n8n later**: optional webhooks from this service to n8n for non-core automation; this app remains source of truth for `runs` / `run_steps`.

## Code reference

Stage list: `runner/pipeline/definition.py` (`STAGES`).
