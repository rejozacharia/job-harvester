```md
# Job Harvester

Agentic job discovery and ranking for senior data/analytics roles. Pulls postings via SerpAPI (Google Jobs + optional LinkedIn Jobs), optionally enriches from company pages, flags assessment-oriented roles, scores fit with an LLM, exports CSV, and exposes a tiny API.

## Features
- Assessment-aware detection with on/off toggles and score boost.
- Optional full-page scrape to enrich descriptions before detection.
- LLM scoring + 1‑line “Why I’m a fit” blurb (OpenAI/OpenRouter).
- Daily scheduled runs via APScheduler (in-container; no host cron).
- CSV exports + optional Telegram notifications.
- Lightweight FastAPI: `/health`, `/latest`, `/run`.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.api:app --reload --port 8080
```

Run harvest once (locally):
```bash
python -m app.cli --once
```

## Docker
```bash
docker build -t job-harvester:dev .
docker run --rm --env-file .env -p 8080:8080 \
  -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output job-harvester:dev
```

## Deploy on Unraid (Compose/Stack)
Use `docker-compose.yml` in this repo. Edit `.env` first. Then:
```bash
docker compose up -d
```

## API
- `GET /health` → `{ ok: true }`
- `GET /latest?limit=20` → last N items from SQLite
- `POST /run` → triggers a manual harvest now
```
```

---
