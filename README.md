# tasklane-api

A task management REST API built as a deliberate learning project, part of a
structured path back to formal backend fundamentals (auth internals, SQL,
testing, CI/CD) after years of learning mostly on the job.

This is Project 1 of a public study series. Each project targets specific
gaps, not just "another CRUD app." The goal here: understand JWT auth from
the inside out, write real integration tests, and ship a proper CI/CD
pipeline.

## Status

🚧 In progress — follow the journey on [dev.to](#).

## Stack

- **Language/Framework:** Python + FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Auth:** JWT (access + refresh tokens), implemented manually — not using
  a third-party auth provider, on purpose. See [ADR 0001](docs/adr/0001-jwt-manual-implementation.md).
- **Testing:** Pytest, httpx.AsyncClient for integration tests
- **CI/CD:** GitHub Actions
- **Deploy:** Railway

## Features

- User registration and login (JWT access + refresh tokens)
- Task CRUD, scoped to the authenticated user
- Paginated task listing with status filtering
- Input validation on every endpoint
- Automated tests covering auth and data isolation
- CI pipeline running lint + tests on every push

## Why this project

I can solve real production problems (multi-tenant isolation, cache bugs,
data pipelines), but I learned most of it by doing, not by studying the
formal fundamentals first. This project is me closing that gap deliberately,
one concept at a time, documented in public.

## Getting started

```bash
git clone https://github.com/saraivas/tasklane-api.git
cd tasklane-api
cp .env.example .env
docker-compose up -d          # starts Postgres
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

## API overview

| Method | Route            | Description                                       | Auth          |
| ------ | ---------------- | ------------------------------------------------- | ------------- |
| POST   | `/auth/register` | Create a user                                     | No            |
| POST   | `/auth/login`    | Get access + refresh token                        | No            |
| POST   | `/auth/refresh`  | Refresh access token                              | Refresh token |
| GET    | `/tasks`         | List current user's tasks (paginated, filterable) | Yes           |
| POST   | `/tasks`         | Create a task                                     | Yes           |
| GET    | `/tasks/{id}`    | Get a task                                        | Yes           |
| PATCH  | `/tasks/{id}`    | Update a task                                     | Yes           |
| DELETE | `/tasks/{id}`    | Delete a task                                     | Yes           |
| GET    | `/health`        | Health check                                      | No            |

## Architecture decisions

Documented as they're made, in [`docs/adr/`](docs/adr/).

## What's next

Project 2 will build on this with multi-tenancy, caching, and async task
processing.

## License

MIT
