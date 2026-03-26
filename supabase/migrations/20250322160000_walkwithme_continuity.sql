-- Walk With Me: character continuity, engagement, editorial calendar, voice pools, episode_log extensions
-- Apply in Supabase SQL editor or via supabase db push.
-- n8n should use the service_role key OR anon with these policies; tighten policies for production.

-- ---------------------------------------------------------------------------
-- editorial_calendar (monthly theme owner)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.editorial_calendar (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  month_start date NOT NULL,
  theme_title text NOT NULL,
  theme_summary text,
  scripture_anchors jsonb DEFAULT '[]'::jsonb,
  tone_notes text,
  agent_version text,
  set_by text,
  created_at timestamptz DEFAULT now(),
  UNIQUE (month_start)
);

CREATE INDEX IF NOT EXISTS idx_editorial_calendar_month ON public.editorial_calendar (month_start DESC);

-- ---------------------------------------------------------------------------
-- voice_pools (data-driven presenters; not hardcoded in n8n)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.voice_pools (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  pool_tag text NOT NULL UNIQUE,
  display_label text,
  diction_notes text,
  avoid_list jsonb DEFAULT '[]'::jsonb,
  elevenlabs_voice_id text,
  weight int DEFAULT 1,
  active boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_voice_pools_tag ON public.voice_pools (pool_tag) WHERE active = true;

-- ---------------------------------------------------------------------------
-- character_canon (serialized fiction facts — not every voice needs a row)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.character_canon (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  character_id text NOT NULL UNIQUE,
  character_name text,
  facts_json jsonb DEFAULT '{}'::jsonb,
  canon_summary text,
  open_threads_json jsonb DEFAULT '[]'::jsonb,
  forbidden_retcon_json jsonb DEFAULT '[]'::jsonb,
  last_run_id text,
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_character_canon_character_id ON public.character_canon (character_id);

-- ---------------------------------------------------------------------------
-- character_episodes (append-only snapshots per serialized publish)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.character_episodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id text NOT NULL,
  ministry_date date NOT NULL,
  character_id text NOT NULL,
  episode_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
  arc_note text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_character_episodes_character ON public.character_episodes (character_id, ministry_date DESC);
CREATE INDEX IF NOT EXISTS idx_character_episodes_run ON public.character_episodes (run_id);

-- ---------------------------------------------------------------------------
-- audience_engagement_items (DV080 → DV001 traceable seeds)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.audience_engagement_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform text NOT NULL,
  platform_post_id text,
  platform_comment_id text NOT NULL,
  comment_text_hash text,
  comment_excerpt text,
  classification text,
  severity text,
  story_safe boolean DEFAULT false,
  sentiment_seed text,
  hook_candidate text,
  status text NOT NULL DEFAULT 'unused' CHECK (status IN ('unused', 'used', 'rejected', 'escalated')),
  consumed_run_id text,
  consumed_at timestamptz,
  source_episode_run_id text,
  created_at timestamptz DEFAULT now(),
  UNIQUE (platform, platform_comment_id)
);

CREATE INDEX IF NOT EXISTS idx_engagement_unused ON public.audience_engagement_items (status, story_safe)
  WHERE status = 'unused' AND story_safe = true;

-- ---------------------------------------------------------------------------
-- episode_log extensions (if table exists)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'episode_log') THEN
    ALTER TABLE public.episode_log ADD COLUMN IF NOT EXISTS platform_post_ids jsonb DEFAULT '{}'::jsonb;
    ALTER TABLE public.episode_log ADD COLUMN IF NOT EXISTS episode_format text;
    ALTER TABLE public.episode_log ADD COLUMN IF NOT EXISTS presenter_mode text;
    ALTER TABLE public.episode_log ADD COLUMN IF NOT EXISTS presenter_snapshot jsonb;
    ALTER TABLE public.episode_log ADD COLUMN IF NOT EXISTS media_manifest_uri text;
    ALTER TABLE public.episode_log ADD COLUMN IF NOT EXISTS lesson_tag text;
    ALTER TABLE public.episode_log ADD COLUMN IF NOT EXISTS main_point_hash text;
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- Optional: migrate legacy character_arcs reads into new tables (no drop)
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- RLS (permissive for n8n anon key — replace with service_role-only in prod)
-- ---------------------------------------------------------------------------
ALTER TABLE public.editorial_calendar ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voice_pools ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.character_canon ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.character_episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audience_engagement_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "n8n_editorial_all" ON public.editorial_calendar;
CREATE POLICY "n8n_editorial_all" ON public.editorial_calendar FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "n8n_voice_pools_all" ON public.voice_pools;
CREATE POLICY "n8n_voice_pools_all" ON public.voice_pools FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "n8n_character_canon_all" ON public.character_canon;
CREATE POLICY "n8n_character_canon_all" ON public.character_canon FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "n8n_character_episodes_all" ON public.character_episodes;
CREATE POLICY "n8n_character_episodes_all" ON public.character_episodes FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "n8n_engagement_all" ON public.audience_engagement_items;
CREATE POLICY "n8n_engagement_all" ON public.audience_engagement_items FOR ALL USING (true) WITH CHECK (true);

-- ---------------------------------------------------------------------------
-- Seed: sample voice pools + placeholder month (adjust month_start)
-- ---------------------------------------------------------------------------
INSERT INTO public.voice_pools (pool_tag, display_label, diction_notes, weight)
VALUES
  ('pastoral_teacher', 'Pastoral teacher', 'Warm, clear, non-performative', 1),
  ('street_wise_uncle', 'Street-wise uncle', 'Plain speech, earned wisdom', 1),
  ('young_parent', 'Young parent voice', 'Tired but faithful', 1),
  ('poet', 'Poetic reflection', 'Sparse, image-led', 1)
ON CONFLICT (pool_tag) DO NOTHING;

INSERT INTO public.editorial_calendar (month_start, theme_title, theme_summary, scripture_anchors, tone_notes, set_by)
VALUES (
  date_trunc('month', (CURRENT_DATE AT TIME ZONE 'America/New_York')::date)::date,
  'Faithfulness in ordinary days',
  'God''s presence in routine pressure and small obedience.',
  '["Psalm 23", "Lamentations 3:22-23"]'::jsonb,
  'Grounded hope; avoid hype.',
  'migration_seed'
)
ON CONFLICT (month_start) DO NOTHING;
