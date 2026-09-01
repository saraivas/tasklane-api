# 0007. Test database schema recreated per test, not transactional rollback

## Status

Accepted

## Context

Looking at [tests/conftest.py](../../tests/conftest.py), the `db_session`
fixture (`scope="function"`) runs `Base.metadata.create_all(bind=engine)`
before yielding a session and `Base.metadata.drop_all(bind=engine)` after
the test finishes — for every single test. The engine points at a
dedicated test database (`tasklane_test`) rather than the database used in
development, and CI
([.github/workflows/ci.yml](../../.github/workflows/ci.yml)) spins up a
fresh `postgres:16` service container with `POSTGRES_DB: tasklane_test` for
every run.

A common alternative for test isolation is to create the schema once for
the whole test session, wrap each test in a transaction, and roll that
transaction back at teardown instead of touching DDL per test — this
avoids repeating `CREATE TABLE`/`DROP TABLE` for every test and is
generally faster as a suite grows.

## Decision

Recreate the full schema for every test function via `create_all` /
`drop_all`, handing the test a real `Session` — not one wrapped in an
outer transaction the test can't see — so route handlers can call
`db.commit()` exactly as they do in production code, with no special
handling for tests.

## Consequences

**Positive**

- Each test starts from a genuinely empty, freshly created schema — no
  risk of state leaking between tests via a forgotten `rollback()` or a
  test whose `commit()` breaks an outer-transaction isolation trick.
- Route code and test code see identical commit behavior. The
  transaction-rollback pattern instead requires nesting a SAVEPOINT under
  an outer transaction and rebinding session events so the app's own
  `commit()` calls don't end isolation early — real complexity added just
  to keep a test-only concern from leaking into how transactions behave.
  This project keeps that at zero.
- The whole mechanism is visible in one place —
  [tests/conftest.py](../../tests/conftest.py) — with nothing implicit
  happening around commit/rollback.

**Negative**

- Slower as the suite grows: every test pays for `CREATE TABLE` /
  `DROP TABLE` across every table, instead of a cheap `ROLLBACK`. At the
  current test count this is unnoticeable; it becomes real cost at
  hundreds of tests.
- Tests can't run in parallel against the same test database without
  colliding, since the schema itself — not just its data — is being
  created and destroyed per test.

## Future improvements

If the suite grows enough for per-test `create_all`/`drop_all` to become a
noticeable cost, the SAVEPOINT-based nested-transaction pattern (create the
schema once per session, wrap each test in a rollback-only transaction
bound to a SAVEPOINT so the app's own `commit()` calls don't end it early)
is the natural next step. It costs more code, but the trade-off starts
paying for itself once schema recreation overhead outweighs that added
complexity.
