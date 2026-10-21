# CLAUDE.md

Context for AI assistants (and humans) working in this repository.

## What this is

`tasklane-api` is Project 1 of a public study series: a task management REST
API (FastAPI, SQLAlchemy 2, PostgreSQL, JWT implemented by hand). It is a
portfolio project, so what the README, the ADRs and the diagrams say must be
true. The owner reviews and merges every pull request.

## The rule that matters most

**Documentation, diagrams and public text describe only what is implemented
and verified in the code.** Nothing is embellished or "planned" inside the
description of current behaviour.

- If the docs and the code disagree, say so. Then either fix the code (with a
  test and an ADR) or fix the docs, and state which one you chose and why.
- Do not claim a number, a test result or a deployment you did not check.
- Planned work goes under "Known limitations" or an ADR's "Future
  improvements", never in the description of what exists.
- This is a public study project. Do not mention employers, clients or
  internal projects.

## Commands

```bash
docker compose up -d db                                       # Postgres on :5433
docker compose exec db createdb -U tasklane tasklane_test     # once
alembic upgrade head                                          # dev database
uvicorn app.main:app --reload
pytest                                                        # uses TEST_DATABASE_URL
```

**Never point `TEST_DATABASE_URL` at a database you care about.** The test
fixtures create and drop every table on each test. `tests/conftest.py` refuses
to run unless the database name ends with `_test`. `DATABASE_URL` is the
application's database (development, or production when running migrations)
and the tests do not use it.

## Layout

- `app/main.py` creates the app and includes the routers.
- `app/routers/auth.py`, `app/routers/tasks.py` hold the endpoints.
- `app/deps.py` has `get_current_user`.
- `app/core/security.py` has password hashing and JWT creation and decoding.
- `app/core/config.py` reads the environment.
- `app/models/`, `app/schemas/` hold SQLAlchemy models and Pydantic schemas.
- `alembic/versions/` holds migrations. `docs/adr/` holds the decisions.
- `tests/unit/` and `tests/integration/` (FastAPI `TestClient`).

## Conventions

- Follow the style of the file you are editing (indentation differs between
  files).
- Every behaviour change comes with tests. Check that a new test can fail:
  break the code on purpose and confirm the test catches it.
- Architecture decisions are ADRs in `docs/adr/`, numbered in order. Do not
  rewrite an old ADR. When it turns out to be wrong or outdated, add an
  `Update` note under its Status, keep the original text, and write a new
  ADR.
- A change that alters a flow updates the diagrams in `README.md` in the same
  pull request. Check Mermaid syntax before committing.
- Commit messages are in English, in the `feat:`, `fix:`, `docs:`, `test:`,
  `ci:` style, and explain why, not only what.
- Work on a branch and open a pull request. Do not push to `main`.
- No secrets in the repository. `.env` is ignored. `.env.example` has only
  placeholders.

## Known limitations

See the README. In short: refresh tokens are not single-use and sessions
cannot be revoked (ADR 0010), there is no rate limiting, database access is
synchronous, and production migrations are run by hand.
