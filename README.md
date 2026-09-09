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
- Problem selection and the web interface are not built yet.

## Tech stack

- Backend: Python, FastAPI, httpx, pytest
- Frontend: Vue 3
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
