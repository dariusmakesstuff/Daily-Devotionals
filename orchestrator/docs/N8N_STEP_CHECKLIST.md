# n8n → orchestrator step checklist

Parsed from exported workflows in `.vscode/`. Maps each actionable node to a **target service module**, **integration deps**, and **idempotency** notes for the custom runner.

## DV001 Daily Devotional Orchestrator

| # | Node name | n8n type | Target module (orchestrator) | Integration | Idempotency |
|---|-----------|----------|------------------------------|-------------|-------------|
| 1 | 🚨 Slack: Error Alert | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 2 | 💾 Supabase: Get Used Combos | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 3 | 🔄 Normalize: Used Combos | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 4 | 📋 Format Used Combos | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 5 | ⏰ Daily Trigger (6 AM ET) | `scheduleTrigger` | API trigger / external scheduler → `POST /runs` | Cron schedule | Trigger: dedupe via idempotency_key on run create |
| 6 | 🔍 Check Today's Episode | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 7 | 🔄 Normalize: Episode Check | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 8 | ⛔ IF: Skip If Ran Today? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 9 | Set Global Config | `set` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Set fields | Stateless or re-entrant if inputs frozen in run snapshot |
| 10 | 🔀 Entry Mode Router | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 11 | GET: YouVersion Verse of Day | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 12 | 📰 GET: World News Headlines | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 13 | 📅 Build Daily Context | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 14 | 🎥 GET: YouTube Testimonies | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 15 | 🎙️ Media Worker: YouTube transcript | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 16 | 🎨 Audience Framing Agent | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 17 | ✍️ Scriptwriter Agent | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 18 | 🛡️ Theology Guardrail (Script) | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 19 | 🎤 ElevenLabs: Host Voice | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 20 | ☁️ Upload Host Audio to GCS | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 21 | 🔀 Assembly Mode Router1 | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 22 | 🎧 Slack: Audio Preview | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 23 | 🔗 Custom Story Webhook | `webhook` | API trigger / external scheduler → `POST /runs` | Webhook trigger | Trigger: dedupe via idempotency_key on run create |
| 24 | 🛰️ OpenAI Web Signal Scout | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 25 | 🔀 Merge: Voice Tracks Ready | `merge` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Merge | Stateless or re-entrant if inputs frozen in run snapshot |
| 26 | ✅ Script Theologically Approved? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 27 | Parser: Framing Output | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 28 | Parser: Script Output | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 29 | Parser: Guardrail-2 Output | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 30 | 📦 Build: Audio Preview Payload | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 31 | 🟠 Fetch: Hacker News Bundle | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 32 | 🎤 ElevenLabs: Reflection Voice | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 33 | ☁️ Upload Reflection Audio to GCS | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 34 | LLM: Framing (Claude Sonnet)1 | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 35 | LLM: Script (Claude Sonnet)1 | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 36 | LLM: Guardrail-2 (Claude Sonnet)1 | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 37 | 🔀 Merge: All World Signals | `merge` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Merge | Stateless or re-entrant if inputs frozen in run snapshot |
| 38 | 💾 Supabase: Save Character Arc | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 39 | ✍️ Voice Writer Agent | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 40 | Build Slack Approval Message | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 41 | 📤 Upload Post: Multi-Platform Video | `uploadPost` | `publish/*` behind registry | Upload Post / social publish | Publish: dedupe by platform + content hash |
| 42 | 📖 Research Agent | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 43 | 🔧 Attach Research Generation | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 44 | 🛡️ Theology Guardrail (Research) | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 45 | ✅ Research Approved? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 46 | 📜 GET: Wikipedia Hymn Search | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 47 | 🎧 Extract Audio URL1 | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 48 | 📊 Log Run to Google Sheets | `googleSheets` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Google Sheets | Stateless or re-entrant if inputs frozen in run snapshot |
| 49 | 🔀 IF: Publishing via Upload-Post? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 50 | 🔧 Upload-Post: Prepare Item | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 51 | IF: Upload-Post Has Targets? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 52 | 🎥 Extract Final Video URL | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 53 | 📝 Platform Caption Formatter | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 54 | 🎨 REMIX Blender | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 55 | 🔧 Shape Theology Reject Row | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 56 | 📋 Log Research Theology Reject | `googleSheets` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Google Sheets | Stateless or re-entrant if inputs frozen in run snapshot |
| 57 | 🔧 Research Theology Reject Handler | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 58 | 🌅 Select Background Loop | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 59 | 🎤 Cast TTS | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 60 | 📌 Upload-Post: Skip (No Platforms) | `set` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Set fields | Stateless or re-entrant if inputs frozen in run snapshot |
| 61 | Parser: Voice Script | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 62 | Parser: Research Output | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 63 | Parser: Guardrail-1 Output | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 64 | ✅ Assembly Ready? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 65 | 🎞️ Build Assembly Payload | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 66 | 🎬 Shotstack: Submit Assembly | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 67 | ⏳ Wait for Shotstack (60s) | `wait` | `runner/pipeline/runner.py` long-step + detail poll state | Wait / poll | Persist poll token on run_step.detail; resume safe |
| 68 | 🔍 Poll Shotstack Status | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 69 | 🌐 Merge Signal Source | `merge` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Merge | Stateless or re-entrant if inputs frozen in run snapshot |
| 70 | 💾 Supabase: Get Last Arc | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 71 | 🔄 Coerce: Last Arc HTTP Output | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 72 | 🔄 Normalize: Last Arc | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 73 | 📅 Supabase: Get Editorial Calendar | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 74 | 💬 Supabase: Get Engagement Seeds | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 75 | 📚 Supabase: Get Character Canon | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 76 | 📦 Assemble Supabase Context Pack | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 77 | 🧹 Prep: Character Memory Input | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 78 | 🧵 Character Memory Agent | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 79 | 🔗 Merge Platform Results | `merge` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Merge | Stateless or re-entrant if inputs frozen in run snapshot |
| 80 | 🗂️ Init Custom Story | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 81 | 💾 Supabase: Get Used Combos (Story) | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 82 | 🔄 Normalize: Used Combos (Story) | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 83 | 📋 Format Used Combos (Story) | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 84 | ✅ Final Notification | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 85 | 🧠 Story Architect | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 86 | 🎯 Signal Agent | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 87 | 🔧 Compose Research Request | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 88 | IF: Research Theology Exhausted? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 89 | 🎞️ Build Short Cut Payload | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 90 | IF: Post YouTube? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 91 | ▶️ Upload to YouTube | `youTube` | `publish/*` behind registry | YouTube | Publish: dedupe by platform + content hash |
| 92 | LLM: Voice Writer | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 93 | LLM: Research | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 94 | LLM: Guardrail-1 (Claude Sonnet)1 | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 95 | 📻 GET: Reddit - Theology | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 96 | Parser: Character Memory | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 97 | 📨 Send Slack Approval Request | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 98 | ⏳ Wait for Human Approval | `wait` | `runner/pipeline/runner.py` long-step + detail poll state | Wait / poll | Persist poll token on run_step.detail; resume safe |
| 99 | ✅ Human Approved? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 100 | 🔔 Notify: Human Rejected | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 101 | 📻 Update Podcast RSS Feed | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 102 | ☁️ Upload RSS Feed to GCS | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 103 | 🔀 Build Platform Publish Queue | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 104 | 📱 TikTok: Init Upload | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 105 | Parser: Story Brief | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 106 | Parser: Signal Output | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 107 | 🔔 Notify: Script Rejected | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 108 | IF: Post TikTok? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 109 | 🎤 ElevenLabs: Host Short Cut | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 110 | ☁️ Upload Host Short Cut to GCS | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 111 | 📻 GET: Reddit - ChristianDating | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 112 | 📝 Format Custom Story Brief | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 113 | 🌱 Seed Interpreter Agent | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 114 | 🎬 Shotstack: Submit Short Cut | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 115 | 🔀 Merge: Short Cut Audio Ready | `merge` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Merge | Stateless or re-entrant if inputs frozen in run snapshot |
| 116 | LLM: Character Memory | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 117 | 📤 Upload to Blotato1 | `blotato` | `publish/*` behind registry | Upload Post / social publish | Stateless or re-entrant if inputs frozen in run snapshot |
| 118 | 🎵 Post to TikTok1 | `blotato` | `publish/*` behind registry | Upload Post / social publish | Stateless or re-entrant if inputs frozen in run snapshot |
| 119 | LLM: Story Architect | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 120 | LLM: Signal | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 121 | 🎤 ElevenLabs: Reflection Short Cut | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 122 | ☁️ Upload Reflection Short Cut to GCS | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 123 | 🔔 Notify: Research Rejected | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 124 | 📻 GET: Reddit - AskBlackPeople | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 125 | Anthropic Chat Model1 | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 126 | IF: Post Instagram? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 127 | 📸 Instagram: Create Reel Container | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 128 | ⏳ Wait for IG Container | `wait` | `runner/pipeline/runner.py` long-step + detail poll state | Wait / poll | Persist poll token on run_step.detail; resume safe |
| 129 | 📸 Instagram: Publish Reel | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 130 | ⏳ Wait 60s More (Assembly) | `wait` | `runner/pipeline/runner.py` long-step + detail poll state | Wait / poll | Persist poll token on run_step.detail; resume safe |
| 131 | 📻 GET: Reddit - MensLib | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 132 | IF: Post Facebook? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 133 | 📘 Facebook: Publish Page Video | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 134 | 🎬 Render Podcast Video | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 135 | 📻 GET: Reddit - AskMen30 | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 136 | 💾 Supabase: Log Episode | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 137 | 💾 Post-Publish: Sync Canon + Episodes + Engagement | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 138 | 💾 Supabase: Log Used Combo | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 139 | 📻 GET: Reddit - BlackMen | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 140 | 💾 Store Clip URI | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 141 | ✅ Clip Ready? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 142 | 💾 Supabase: Store Clip URI | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 143 | ✅ All Clips Done? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 144 | 📦 Fetch All Clips for Assembly | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 145 | ☁️ Upload Rendered Podcast to GCS | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 146 | 🔀 Production Mode Router | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 147 | 🎬 Visual Director Agent | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 148 | 📋 Split Scenes for Veo Loop | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 149 | 🎥 Submit Veo 3 Job (Vertex AI)1 | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 150 | ⏳ Wait 30s for Veo Rendering1 | `wait` | `runner/pipeline/runner.py` long-step + detail poll state | Wait / poll | Persist poll token on run_step.detail; resume safe |
| 151 | 🔍 Poll Veo Operation Status1 | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 152 | 📡 Fetch: Reddit Men's Loop (AskMen/daddit/jobs/Marriage) | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 153 | ⏳ Wait 30s More1 | `wait` | `runner/pipeline/runner.py` long-step + detail poll state | Wait / poll | Persist poll token on run_step.detail; resume safe |
| 154 | 📻 GET: Reddit - MenRelationships | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 155 | LLM: Visual | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 156 | Parser: Visual Output | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 157 | 📻 GET: Reddit - Positivity | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 158 | Anthropic Chat Model | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 159 | 🔑 Reddit: Client Token | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |

## DV080 Social Engagement Orchestrator

| # | Node name | n8n type | Target module (orchestrator) | Integration | Idempotency |
|---|-----------|----------|------------------------------|-------------|-------------|
| 1 | 🚨 Escalate to Human (Slack) | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 2 | ⏰ Poll Comments (Every 30 Min) | `scheduleTrigger` | API trigger / external scheduler → `POST /runs` | Cron schedule | Trigger: dedupe via idempotency_key on run create |
| 3 | 📥 Simulate / Load New Comments | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 4 | 🏷️ Comment Classifier | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 5 | 📦 Shape Engagement Row | `code` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Code transform | Stateless or re-entrant if inputs frozen in run snapshot |
| 6 | 💾 Supabase: Insert Engagement | `httpRequest` | `integrations/*` REST client | HTTP (Supabase, APIs) | Use If-None-Match / idempotent POST where API supports |
| 7 | 🚨 Escalate? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 8 | 💬 Engager Agent | `agent` | `llm_provider` + stage prompt | LLM agent | Stateless or re-entrant if inputs frozen in run snapshot |
| 9 | ✅ Should Publish Reply? | `if` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Branch | Stateless or re-entrant if inputs frozen in run snapshot |
| 10 | 📊 Log Comment to Google Sheets | `googleSheets` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | Google Sheets | Stateless or re-entrant if inputs frozen in run snapshot |
| 11 | LLM: Classifier | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 12 | Parser: Classification | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
| 13 | LLM: Engager | `lmChatOpenAi` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | LLM chat model | Stateless or re-entrant if inputs frozen in run snapshot |
| 14 | Parser: Engager Output | `outputParserStructured` | TBD map in `runner/pipeline/stage_handlers.py` + integrations | — | Stateless or re-entrant if inputs frozen in run snapshot |
