/*
# Create Review Intelligence tables (reviews, analyses, model_performance)

1. New Tables
- `reviews`
  - `id` (uuid, primary key, auto-generated)
  - `review_text` (text, not null) — the raw customer review text
  - `sentiment` (text, nullable) — 'positive' | 'negative' | 'neutral'; null until the ML backend classifies it
  - `confidence` (real, nullable) — 0..1 classifier confidence; null until ML backend exists
  - `product_name` (text, nullable) — product the review refers to
  - `created_at` (timestamptz, defaults to now)
- `analyses`
  - `id` (uuid, primary key, auto-generated)
  - `total_reviews` (integer, not null) — number of reviews in the batch
  - `positive_count` (integer, not null, default 0)
  - `negative_count` (integer, not null, default 0)
  - `neutral_count` (integer, not null, default 0)
  - `created_at` (timestamptz, defaults to now)
- `model_performance`
  - `id` (uuid, primary key, auto-generated)
  - `model_name` (text, not null) — e.g. 'Linear SVM'
  - `accuracy` (real, not null) — measured evaluation metric, populated only after real training
  - `precision` (real, not null)
  - `recall` (real, not null)
  - `f1_score` (real, not null)
  - `created_at` (timestamptz, defaults to now)

2. Indexes
- `reviews_created_at_idx` on `reviews(created_at)` for recent-activity queries.
- `reviews_sentiment_idx` on `reviews(sentiment)` for sentiment counts.
- `model_performance_model_name_idx` on `model_performance(model_name)`.
- `model_performance_created_at_idx` on `model_performance(created_at)` to fetch latest evaluation per model.

3. Security
- Enable RLS on all three tables.
- This app has no sign-in: data is intentionally shared, so policies allow anon + authenticated CRUD.
- Grants: SELECT on all tables to anon + authenticated; INSERT/UPDATE/DELETE on reviews to anon + authenticated;
  SELECT+INSERT on analyses; SELECT on model_performance (metrics are written by the backend/DBA only).
- sentiment CHECK constraint allows only 'positive', 'negative', 'neutral' or null.
- confidence CHECK constraint restricts values to 0..1.

4. Important Notes
- No ML is implemented: sentiment/confidence are nullable so the API can store reviews before classification.
- model_performance has no seed data — real metrics will be inserted only after actual model evaluation.
*/

CREATE TABLE IF NOT EXISTS reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  review_text text NOT NULL,
  sentiment text CHECK (sentiment IN ('positive', 'negative', 'neutral')),
  confidence real CHECK (confidence >= 0 AND confidence <= 1),
  product_name text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analyses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  total_reviews integer NOT NULL CHECK (total_reviews >= 0),
  positive_count integer NOT NULL DEFAULT 0 CHECK (positive_count >= 0),
  negative_count integer NOT NULL DEFAULT 0 CHECK (negative_count >= 0),
  neutral_count integer NOT NULL DEFAULT 0 CHECK (neutral_count >= 0),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS model_performance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model_name text NOT NULL,
  accuracy real NOT NULL,
  precision real NOT NULL,
  recall real NOT NULL,
  f1_score real NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS reviews_created_at_idx ON reviews (created_at);
CREATE INDEX IF NOT EXISTS reviews_sentiment_idx ON reviews (sentiment);
CREATE INDEX IF NOT EXISTS model_performance_model_name_idx ON model_performance (model_name);
CREATE INDEX IF NOT EXISTS model_performance_created_at_idx ON model_performance (created_at);

ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_performance ENABLE ROW LEVEL SECURITY;

GRANT SELECT ON reviews TO anon, authenticated;
GRANT INSERT, UPDATE, DELETE ON reviews TO anon, authenticated;
GRANT SELECT, INSERT ON analyses TO anon, authenticated;
GRANT SELECT ON model_performance TO anon, authenticated;

DROP POLICY IF EXISTS "select_reviews" ON reviews;
CREATE POLICY "select_reviews" ON reviews
  FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "insert_reviews" ON reviews;
CREATE POLICY "insert_reviews" ON reviews
  FOR INSERT TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "update_reviews" ON reviews;
CREATE POLICY "update_reviews" ON reviews
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "delete_reviews" ON reviews;
CREATE POLICY "delete_reviews" ON reviews
  FOR DELETE TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "select_analyses" ON analyses;
CREATE POLICY "select_analyses" ON analyses
  FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "insert_analyses" ON analyses;
CREATE POLICY "insert_analyses" ON analyses
  FOR INSERT TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "select_model_performance" ON model_performance;
CREATE POLICY "select_model_performance" ON model_performance
  FOR SELECT TO anon, authenticated USING (true);
