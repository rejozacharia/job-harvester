# Job Harvester

Agentic job discovery and ranking for senior data/analytics roles. Pulls postings via SerpAPI (Google Jobs + optional LinkedIn Jobs), optionally enriches from company pages, flags assessment-oriented roles, scores fit with an LLM, exports CSV, and exposes a tiny API.

## Features
- Assessment-aware detection with on/off toggles and score boost.
- Optional full-page scrape to enrich descriptions before detection.
- LLM scoring + 1-line “Why I’m a fit” blurb (OpenAI/OpenRouter or any OpenAI-compatible endpoint).
- Scheduled runs via APScheduler with configurable cron expressions (in-container; no host cron).
- CSV exports + optional Telegram notifications.
- Lightweight FastAPI: `/health`, `/latest`, `/run`, `/dashboard` (live status UI).

## How scoring works

- Each harvested posting is represented as a `Job` model containing title, company, source, description, and other metadata. The raw snippet from SerpAPI can optionally be enriched with a full-page scrape when `ENABLE_FOLLOW_LINK=true`.
- `app/agent.py` contains `LLMScorer`, which calls the configured OpenAI/OpenRouter model or any OpenAI-compatible endpoint to rate strategic fit from 0–100 and generate a short “Why I’m a fit” blurb. The model prompt is tailored for senior data and analytics leadership roles.
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
│   ├── scheduler.py      # APScheduler setup for cron-based runs inside the container
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

1. Copy `.env.example` to `.env` and supply secrets (SerpAPI, OpenAI/OpenRouter, custom LLM endpoint, Telegram, etc.).
2. Adjust search titles, keywords, and locations to match the roles you want to target.
   - To cover multiple regions, list them in `LOCATIONS` as a comma-separated string (e.g. `Remote,New York, NY, USA,San Francisco, CA, USA,Bengaluru, India,Dubai, UAE`). The runner iterates over every title/location combination.
3. Toggle optional features such as assessment filtering/boosting and link-following as needed.
4. Adjust `SCHEDULE_CRONS` (comma/semicolon/newline separated) to control how often the harvester runs. Example: `SCHEDULE_CRONS=0 */4 * * *` runs every 4 hours; multiple expressions are supported for precise timing.
5. Customize `JOB_STATUS_CHOICES` if you want different lifecycle buckets for tracking applications.

### Configuring LLM connectivity

- Set `LLM_MODEL` to any model identifier supported by your provider (defaults to `gpt-4o-mini`).
- To target a self-hosted or proxy endpoint (Ollama, LM Studio, etc.), set `LLM_API_BASE` to its OpenAI-compatible base URL (for example `http://localhost:11434/v1`).
- Provide `LLM_API_KEY` if the endpoint expects a bearer token. When omitted, the client supplies a placeholder token so most local gateways accept the request without extra setup.
- If no custom base URL is supplied, the harvester falls back to `OPENAI_API_KEY` and `OPENROUTER_API_KEY` in that order.

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

The API (and dashboard) will be available at `http://localhost:8080`.  Useful endpoints include:

- `GET /health` – liveness probe for Docker and health checks
- `GET /latest?limit=20` – newest records from SQLite as JSON
- `POST /run` – trigger a harvest immediately
- `POST /jobs/{job_id}/status` – update the lifecycle status/notes for a stored job (e.g. applied, rejected)

### Web dashboard & status updates

- Visit `http://localhost:8080/dashboard` (or simply `/`) for a lightweight UI that lists the newest jobs, sorted by insertion time.
- The dashboard refreshes automatically every 30 seconds and shows LLM scores, assessment flags, and source metadata.
- Each row exposes a status dropdown plus notes field; hit **Save** to persist through the same `/jobs/{id}/status` API used by automation.
- Configure the number of rows displayed via `DASHBOARD_LIMIT` in `.env`.

### Job lifecycle & deduplication

- Each SerpAPI result is hashed (URL + metadata) into a deterministic ID before insertion. SQLite enforces this as the primary key, so the same posting will only be stored once even if it appears in later runs.
- Newly inserted rows default to the `harvested` lifecycle state. Use the `/jobs/{id}/status` endpoint to move them into other states (`applied`, `rejected`, etc.) and to attach free-form notes.
- Status values are validated against `JOB_STATUS_CHOICES` to keep downstream exports consistent; tweak the list in `.env` if you prefer different labels.

## Scheduler behaviour

`main.py` starts the FastAPI app and launches the background scheduler. Cron expressions come from the `SCHEDULE_CRONS`
setting (defaults to `40 7 * * *` for 07:40 America/Chicago). Provide multiple expressions to run several times per day;
invalid expressions are ignored and the default is used as a fallback.

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
