-- Optional flags for tragedy-day / pause fiction (editorial-ops from plan)
CREATE TABLE IF NOT EXISTS public.system_flags (
  key text PRIMARY KEY,
  value_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE public.system_flags ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "n8n_system_flags_all" ON public.system_flags;
CREATE POLICY "n8n_system_flags_all" ON public.system_flags FOR ALL USING (true) WITH CHECK (true);

INSERT INTO public.system_flags (key, value_json)
VALUES ('editorial', '{"pause_fiction": false, "somber_mode": false}'::jsonb)
ON CONFLICT (key) DO NOTHING;
