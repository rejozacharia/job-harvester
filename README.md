# Job Harvester

Agentic job discovery and ranking for senior data/analytics roles. Pulls postings via SerpAPI (Google Jobs + optional LinkedIn Jobs), optionally enriches from company pages, flags assessment-oriented roles, scores fit with an LLM, exports CSV, and exposes a tiny API.

## Features
- Assessment-aware detection with on/off toggles and score boost.
- Optional full-page scrape to enrich descriptions before detection.
- LLM scoring + 1-line “Why I’m a fit” blurb (OpenAI/OpenRouter).
- Daily scheduled runs via APScheduler (in-container; no host cron).
- CSV exports + optional Telegram notifications.
- Lightweight FastAPI: `/health`, `/latest`, `/run`.

## How scoring works

- Each harvested posting is represented as a `Job` model containing title, company, source, description, and other metadata. The raw snippet from SerpAPI can optionally be enriched with a full-page scrape when `ENABLE_FOLLOW_LINK=true`.
- `app/agent.py` contains `LLMScorer`, which calls the configured OpenAI or OpenRouter model to rate strategic fit from 0–100 and generate a short “Why I’m a fit” blurb. The model prompt is tailored for senior data and analytics leadership roles.
- Assessment-oriented language is detected locally (no LLM call required) and can be used to filter or boost scores via `.env` toggles.

## Project structure

```text
.
├── app/
│   ├── api.py            # FastAPI routes for health check, latest jobs, manual run trigger
│   ├── agent.py          # LLM scoring client and assessment-term helpers
│   ├── cli.py            # Command-line entry point for ad-hoc harvests
│   ├── db.py             # SQLite initialization and upsert helpers
│   ├── harvest.py        # Core Runner pipeline, CSV exporter, and storage wrapper
│   ├── models.py         # Pydantic Job schema shared by the app
│   ├── scrape.py         # Optional full-page scraping of job postings
│   ├── scheduler.py      # APScheduler setup for daily runs inside the container
│   ├── settings.py       # Pydantic-settings backed configuration (reads `.env`)
│   └── sources.py        # SerpAPI-powered Google Jobs & LinkedIn Jobs loaders
├── main.py               # ASGI application that mounts the API and starts the scheduler
├── requirements.txt      # Runtime dependencies for FastAPI, APScheduler, SerpAPI client, etc.
├── Dockerfile            # Production container image definition (uvicorn + healthcheck)
├── docker-compose.yml    # Example deployment with persistent volumes + watchtower
├── .env.example          # Template of required configuration values
└── .github/workflows/    # CI workflow publishing images to GHCR
```

Data produced at runtime is written to `data/` (SQLite database) and `output/` (CSV exports).

## Configuration

1. Copy `.env.example` to `.env` and supply secrets (SerpAPI, OpenAI/OpenRouter, Telegram, etc.).
2. Adjust search titles, keywords, and locations to match the roles you want to target.
   - To cover multiple regions, list them in `LOCATIONS` as a comma-separated string (e.g. `Remote,New York, NY, USA,San Francisco, CA, USA,Bengaluru, India,Dubai, UAE`). The runner iterates over every title/location combination.
3. Toggle optional features such as assessment filtering/boosting and link-following as needed.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # update values inside
uvicorn app.api:app --reload --port 8080
```

Run a one-off harvest from the CLI:

```bash
python -m app.cli --once
```

The API will be available at `http://localhost:8080`.  Useful endpoints include:

- `GET /health` – liveness probe for Docker and health checks
- `GET /latest?limit=20` – newest records from SQLite as JSON
- `POST /run` – trigger a harvest immediately

## Scheduler behaviour

`main.py` starts the FastAPI app and launches the background scheduler. By default, the
APScheduler job executes daily at 07:40 America/Chicago. Modify `app/scheduler.py`
if you need different timing.

## Docker usage

Build and run locally:

```bash
docker build -t job-harvester:dev .
docker run --rm --env-file .env -p 8080:8080 \
  -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output job-harvester:dev
```

> **Note:** The Docker build step only needs the source tree and `requirements.txt`. A populated `.env` file is required at runtime (passed via `--env-file` or Compose) but not during `docker build`.

## Deploy on Unraid (Compose/Stack)

Use the bundled `docker-compose.yml`. Edit `.env` first, then:

```bash
docker compose up -d
```

The compose file also includes [containrrr/watchtower](https://containrrr.dev/watchtower/) to keep
the container image updated from GHCR.
