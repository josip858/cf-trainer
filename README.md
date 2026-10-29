# Codeforces Trainer

Picks daily Codeforces practice problems at the right difficulty, so training time
goes into solving rather than searching.

## Motivation

A daily competitive programming routine starts with the same chore: open the
Codeforces problemset, filter by rating, and check which problems have already been
solved. Codeforces Trainer automates that step — given a handle, it reads the user's
rating and solved problems from the Codeforces API and returns unsolved problems
slightly above their current level.

## Status

version 0 — in progress.

- The backend fetches user rating, solved problems and the full problemset from the
  Codeforces API.
- Problem selection is implemented through `GET /api/picks?handle=YOUR_HANDLE`.
- The problemset is cached in memory for the current server calendar day.
  Outgoing Codeforces requests are paced with a minimum interval of 2.1 seconds.
- User-facing error handling and the Vue web interface are still in progress.

## Selection rules

- Round the user's rating to the nearest hundred.
  Users without a rating, or with a rating below 700, use a base of 700.
- Select up to two unsolved problems at base + 100 and one at base + 300,
  prioritizing higher `solvedCount` within each bucket.
- Include `rating_source` (`cf` or `assumed`) alongside the selected problems.

The picker does not make network requests. `cf_client.py` handles Codeforces
integration, `schemas.py` defines the data contracts, and `main.py` connects them.

## Tech stack

- Backend: Python, FastAPI, httpx, pytest
- Frontend: Vue 3 (planned)
- Deployment: Render

## Running locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
fastapi dev main.py
```

Run the tests. The `not slow` marker skips the tests that call the Codeforces API,
so the suite runs offline:

```bash
pytest -m "not slow"
```

## API

- `GET /` — health check
- `GET /api/picks?handle=YOUR_HANDLE` — select practice problems
- `/docs` — interactive API documentation

The picks endpoint currently implements the successful request path. Input
validation and mapping Codeforces errors to user-facing HTTP responses are the
next backend task.
