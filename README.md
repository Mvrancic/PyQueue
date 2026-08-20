# PyQueue

**A lightweight, self-hosted task queue & job processing system**, built with FastAPI, Redis, and PostgreSQL.

PyQueue lets you enqueue background jobs over a REST API, process them asynchronously with a decoupled worker, and track their status, results, and failures — with automatic retries built in.

## Features

- **Job Management API** — create, retrieve, list, cancel, and retry jobs over REST.
- **Async Background Processing** — a standalone worker consumes jobs from a Redis queue, independent of the API process.
- **Persistence** — job state, payload, results, and errors are stored in PostgreSQL.
- **Automatic Retries** — failed jobs are re-queued up to a configurable `max_retries`, with retry count tracked per job.
- **Pluggable Job Types** — handlers are registered in a task registry, so adding a new job type is a matter of writing one function.
- **Dockerized** — API, worker, PostgreSQL, and Redis all run via a single `docker-compose up`.

## Architecture

```
        POST /jobs                 BRPOP
Client ────────────► API ──────► Redis ──────► Worker ──────► Handler
                       │  (FastAPI)  (queue)              (sleep/csv_stats/...)
                       │
                       ▼
                  PostgreSQL
              (job state & results)
```

| Component  | Responsibility                                                        |
|------------|------------------------------------------------------------------------|
| API        | FastAPI app that accepts job requests and exposes job status endpoints |
| Redis      | Lightweight queue buffering job IDs between API and worker             |
| Worker     | Long-running process that dequeues jobs (`BRPOP`) and executes them    |
| PostgreSQL | Source of truth for job state, payloads, results, and errors           |

## Tech Stack

Python 3.11 · FastAPI · SQLAlchemy · Alembic · Redis · PostgreSQL · Docker Compose · Pytest

## Technical Decisions and Known Limitations

**Redis as buffer, PostgreSQL as source of truth.** The queue only carries job
IDs; all state lives in Postgres. This lets the system rebuild its state even
if Redis is lost, at the cost of one extra query per job.

**At-most-once semantics (known limitation).** The worker does `BRPOP` and then
updates state in the database. If the process crashes between those two
operations, the job is lost — there is no ack or visibility timeout.
Achieving at-least-once delivery would require an intermediate "in-flight"
queue (the `BRPOPLPUSH` pattern) with a reaper that returns orphaned jobs.

**Cooperative cancellation.** Canceling a RUNNING job marks it in the database
but does not interrupt the handler already in progress. Interrupting it would
require handlers to periodically check a cancellation signal.

**No priorities or scheduling.** A single FIFO queue. Priorities would require
multiple Redis lists; deferred jobs would need a sorted set keyed by timestamp.

## Getting Started

### Prerequisites

- Docker & Docker Compose

### Run it

1. Copy the environment template and adjust if needed:
   ```bash
   cp .env.example .env
   ```

2. Start everything (API, worker, PostgreSQL, Redis):
   ```bash
   docker-compose up --build
   ```

3. Explore the API:
   - Base URL: `http://localhost:8000/api/v1`
   - Interactive docs (Swagger UI): `http://localhost:8000/docs`

### API Reference

| Method | Endpoint                  | Description                       |
|--------|----------------------------|------------------------------------|
| POST   | `/api/v1/jobs`             | Create and enqueue a new job       |
| GET    | `/api/v1/jobs`             | List jobs (filter by `status`)     |
| GET    | `/api/v1/jobs/{job_id}`    | Fetch a single job                 |
| POST   | `/api/v1/jobs/{job_id}/cancel` | Cancel a queued or running job |
| POST   | `/api/v1/jobs/{job_id}/retry`  | Re-queue a failed or canceled job |
| GET    | `/health`                  | Liveness check                     |

### Job Types

| Type        | Payload                    | Description                                          |
|-------------|-----------------------------|-------------------------------------------------------|
| `sleep`     | `{ "seconds": 3 }`          | Simulates a slow task by sleeping for N seconds       |
| `csv_stats` | `{ "csv_text": "..." }`     | Parses CSV text and returns row/column stats          |
| `fail`      | `{}`                        | Always fails — useful for testing the retry pipeline  |

### Usage Examples

**Create a job:**
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "csv_stats",
    "payload": { "csv_text": "id,name,score\n1,Alice,90\n2,Bob,85" },
    "max_retries": 2
  }'
```

**Check status** (replace `JOB_ID` with the id returned above):
```bash
curl "http://localhost:8000/api/v1/jobs/JOB_ID"
```

**Cancel a job:**
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/JOB_ID/cancel"
```

**Retry a failed job:**
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/JOB_ID/retry"
```

## Project Structure

```
src/pyqueue/
├── api/                # FastAPI routes, request/response schemas
├── domain/              # Core enums (JobStatus, JobType)
├── infra/
│   ├── db/              # SQLAlchemy models, session, Alembic migrations
│   └── queue/            # Redis queue client
├── services/            # Business logic (JobService, task registry)
├── workers/              # Worker entrypoint + job handlers
├── config.py             # Environment-based settings
└── main.py                # FastAPI app entrypoint
```

## Development

Run the test suite locally without Docker:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
cp .env.example .env   # required: Settings() reads DATABASE_URL/REDIS_URL at import time
pytest tests/
```

### Database Migrations

Migrations are managed with Alembic:

```bash
alembic upgrade head        # apply migrations
alembic revision --autogenerate -m "message"   # create a new migration
```

## License

This project is provided as-is for educational and portfolio purposes.
