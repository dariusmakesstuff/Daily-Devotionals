-- Optional: apply when using Supabase Postgres as orchestrator DB (not required for local SQLite dev).
-- Correlation IDs, usage logging, integration toggles, encrypted secret metadata, engagement runs.

ALTER TABLE IF EXISTS public.runs ADD COLUMN IF NOT EXISTS correlation_id varchar(64);
CREATE INDEX IF NOT EXISTS idx_runs_correlation_id ON public.runs (correlation_id);

ALTER TABLE IF EXISTS public.run_steps ADD COLUMN IF NOT EXISTS progress_percent int;
ALTER TABLE IF EXISTS public.run_steps ADD COLUMN IF NOT EXISTS external_operation_id varchar(256);

-- If tables live outside Supabase, create fresh:

CREATE TABLE IF NOT EXISTS public.integration_settings (
  key varchar(64) PRIMARY KEY,
  enabled boolean NOT NULL DEFAULT true,
  health_ok boolean,
  config jsonb,
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.app_secrets (
  name varchar(128) PRIMARY KEY,
  ciphertext text NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.provider_usage (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid REFERENCES public.runs(id) ON DELETE SET NULL,
  run_step_id uuid REFERENCES public.run_steps(id) ON DELETE SET NULL,
  provider varchar(32) NOT NULL,
  model varchar(128),
  input_tokens int,
  output_tokens int,
  cost_usd double precision,
  detail jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_provider_usage_run ON public.provider_usage (run_id);

CREATE TABLE IF NOT EXISTS public.notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid REFERENCES public.runs(id) ON DELETE SET NULL,
  channel varchar(32) NOT NULL,
  payload jsonb,
  status varchar(16) NOT NULL DEFAULT 'pending',
  error_message text,
  sent_at timestamptz,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.engagement_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  status varchar(32) NOT NULL DEFAULT 'queued',
  idempotency_key varchar(128) UNIQUE,
  error_message text,
  meta jsonb,
  correlation_id varchar(64),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_engagement_runs_correlation ON public.engagement_runs (correlation_id);

CREATE TABLE IF NOT EXISTS public.engagement_run_steps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES public.engagement_runs(id) ON DELETE CASCADE,
  ordinal int NOT NULL,
  stage_key varchar(64) NOT NULL,
  title varchar(256) NOT NULL,
  status varchar(32) NOT NULL DEFAULT 'pending',
  skipped_reason varchar(512),
  error_message text,
  detail jsonb,
  started_at timestamptz,
  finished_at timestamptz
);
