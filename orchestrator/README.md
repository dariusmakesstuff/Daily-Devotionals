# Walk With Me — Orchestrator (Phase 1 scaffold)

Python **FastAPI** API + **Arq** worker + **Postgres** (runs / steps) + **Redis** (job queue). Stages are **stubs** today; replace each with real LLM/API calls as you port off n8n.

## Quick start (local, no Docker)

Defaults: **SQLite** file `wwm_dev.db` and **`SYNC_WORKER=true`** (no Redis). The API runs the pipeline **inside the POST /runs request** until stubs finish (fine for dev; use Arq in production).

1. Optional: `copy .env.example .env` and adjust.

2. From `orchestrator/`:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   $env:PYTHONPATH = "$PWD"
   uvicorn runner.main:app --reload --host 127.0.0.1 --port 8000
   ```

3. Open **http://127.0.0.1:8000/** → redirects to **`/dashboard`** (small HTML UI to list runs and start new ones).  
   **http://127.0.0.1:8000/docs** — Swagger UI (if it does not load, try **http://127.0.0.1:8000/openapi.json** or another browser; some extensions block Swagger).  
   **http://127.0.0.1:8000/health** — `{"status":"ok"}` if the server is up.

4. **POST /runs** with body `{"output_mode":"audio_only"}`; response includes completed steps when `sync_worker` is on.

## Quick start (Docker: Postgres + Redis + Arq)

1. `docker compose up -d postgres redis` (or full `docker compose up --build` for api+worker).

2. Set `DATABASE_URL` and `REDIS_URL` in `.env`, and **`SYNC_WORKER=false`**.

3. Run API + worker (two processes) as in earlier revisions, or use the full `docker compose` stack.

5. Create a run:

   ```bash
   curl -X POST http://127.0.0.1:8000/runs -H "Content-Type: application/json" -d "{\"output_mode\":\"audio_only\"}"
   ```

   Poll `GET /runs/{id}` to see step progress until `status` is `succeeded`.

## Full stack in Docker

```bash
docker compose up --build
```

API: `http://127.0.0.1:8000` — docs at `/docs`.

## Configuration

| Variable | Meaning |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy URL (`postgresql+psycopg://...`) |
| `REDIS_URL` | Arq broker |
| `REQUIRE_HUMAN_APPROVAL` | `true` = pause at `human_approval_script` until `POST /runs/{id}/resume` |
| `ENCRYPTION_KEY` | Fernet-compatible secret for `POST /secrets` (raw string hashed to key, or `base64:...`) |
| `ORCHESTRATOR_API_KEY` | If set, required as `X-API-Key` for mutating routes (integrations PATCH, secrets, hooks, `POST /engagement-runs`) |
| `RATE_LIMIT_PER_MINUTE` | Per-IP limit (0 = off) |

## API surface (plan alignment)

- `GET/PATCH /integrations` — toggle integrations (`PATCH` needs API key when configured).
- `GET/POST /secrets` — encrypted name/value store (never returns plaintext).
- `POST /hooks/run-completed`, `POST /hooks/n8n/trigger` — queue `notifications` rows for outbound automation.
- `GET/POST /engagement-runs` — DV080-style engagement pipeline (stub steps; `POST` needs API key when configured).
- `GET /health/integrations` — integration snapshot for ops.
- Runs carry `correlation_id` (auto or `RunCreate.correlation_id`); `meta` booleans validated for platform compliance fields.

## Layout

- `runner/pipeline/definition.py` — ordered stages (DV001-aligned).
- `runner/pipeline/runner.py` — executes steps; integration policy skips disabled deps; LLM usage → `provider_usage`.
- `runner/integrations/registry.py` — DB-backed toggles + defaults.
- `runner/storage/` — `ObjectStorage` protocol + local + S3-compatible stub.
- `docs/N8N_STEP_CHECKLIST.md` — DV001/DV080 node inventory.
- `docs/ORCHESTRATION_CHOICE.md` — Arq now, Temporal when scale demands.
- `../media-worker/` — Docker image with **ffmpeg** (worker entrypoint placeholder).

## Next steps

- Wire real TTS, Veo (`runner/integrations/veo.py`), and publish adapters (`runner/integrations/publish.py`).
- Point `DATABASE_URL` at Supabase Postgres and apply `supabase/migrations/20250323120000_orchestrator_extensions.sql` if you unify DBs.
- Process `notifications` with a small sender worker (Slack/email/webhook).
