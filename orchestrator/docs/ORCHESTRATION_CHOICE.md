# Orchestration stack decision

## Decision

**Phase 0–2 (current codebase): Redis + [Arq](https://github.com/samuelcolvin/arq)** for background execution of `runs`, with **optional `SYNC_WORKER=true`** for SQLite-only local dev (in-process `asyncio.to_thread`).

**Phase 3+ (recommended if long-poll / human-wait complexity grows):** evaluate **Temporal** for per-activity retries, durable timers, and first-class visibility—per the product plan’s recommendation when ops tolerance allows an additional operational component.

## Rationale

| Option | Fit for WWM | Notes |
|--------|----------------|-------|
| **Arq** | **Selected now** | Already integrated; minimal moving parts; good enough for queue + worker fan-out; human gates implemented via DB `waiting_human` + resume API. |
| **BullMQ** | Deferred | Strong Node ecosystem; this service is Python-first—would split runtime or add bridge. |
| **Inngest** | Deferred | Managed velocity; vendor coupling and self-host story vs Hetzner-only needs review. |
| **Temporal** | **Future** | Best match for Veo long poll + complex retries; adopt when Arq in-step polling becomes hard to reason about or observe. |

## Consequences

- Runs remain **source of truth in Postgres/SQLite** (`runs`, `run_steps`); workers are stateless beyond the job payload.
- **Idempotency** stays at the API (`idempotency_key`) and must be reinforced per integration (publish, upload).
- A later **Temporal** migration would re-home step execution to activities while **keeping the same tables** for dashboard compatibility, or dual-write during transition.
