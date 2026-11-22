# Project memory

## Product intent & audience

- Sentiment analysis platform for customer reviews: ingest reviews, classify sentiment, surface dashboard stats and model performance.
- Full-stack app with a React frontend, Express API backend, Python ML service, and Supabase PostgreSQL.
- Audience likely internal/analyst users monitoring review sentiment and ML model quality.

## Brand personality & voice

- Pragmatic, honest, engineering-focused communication.
- ML service explicitly reports "no models trained yet" rather than faking results — transparency valued.

## Visual design & UX direction

- Frontend stack: Vite + React (JSX), Tailwind CSS, Lucide React icons.
- Import convention: `@/` path alias maps to `src/`.
- Production-quality, non-cookie-cutter designs expected.
- No extra UI/icon theme packages unless explicitly requested.

## Decisions, constraints & rationale

- Express backend (port 4000) is the single API surface; all DB access routed through it via Prisma, not the Supabase Data API directly.
- DB tables: `reviews`, `analyses`, `model_performance`.
- Reviews created with empty sentiment until ML classifies them.
- Python ML service (port 8000) handles preprocessing, dataset inspection, and model status/performance.
- Model performance endpoints reserved for real ML evaluation runs — no placeholder/synthetic metrics.
- Supabase PostgreSQL connected via `DATABASE_URL` in `backend/.env`.

## Open questions & assumptions

- Express proxy routes to ML service not yet wired: `/api/ml/status`, `/api/reviews/predict`, `/api/reviews/bulk`, `/api/models/metrics`, `/api/insights`.
- ML training and prediction endpoints planned for later phases.
- Frontend integration with the documented API endpoints not yet confirmed from this turn.