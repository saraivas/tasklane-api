# 0009. Offset/limit pagination over cursor-based pagination

## Status

Accepted

## Context

`GET /tasks` needed pagination once a user's task list could grow past what's
reasonable to return in one response. Two common approaches exist: offset/limit
(the caller asks for `page` N and a page `limit`, the server skips `(page-1) *
limit` rows) and cursor-based pagination (the caller passes an opaque pointer
to the last item it saw, the server returns the next batch after that point).

Cursor pagination's main advantage is that it stays constant-time as a table
grows — it doesn't have to scan and discard the rows it's skipping the way a
large `OFFSET` does — and it doesn't miss or duplicate rows when items are
inserted or deleted between page requests. Its main cost is that it can't jump
to an arbitrary page number, since each cursor only knows how to move forward
from wherever the previous page ended.

Tasklane is a single-user-scoped, early-stage learning project. Per-user task
counts are small, and nothing in the current product calls for "jump to page
37" or infinite-scroll-under-heavy-write-load behavior. Cursor pagination's
constant-time advantage doesn't matter yet at this scale, and offset/limit's
missing "jump to page N" isn't needed either — the tradeoff genuinely doesn't
bite in either direction right now.

## Decision

Use offset/limit pagination on `GET /tasks`, implemented in
[app/routers/tasks.py](../../app/routers/tasks.py):

- `page` (default 1, minimum 1) and `limit` (default 20, minimum 1, **maximum
  100**) are query parameters. The max-100 cap exists so a caller can't force
  the server to materialize an unbounded result set in one request.
- `offset = (page - 1) * limit` is computed and passed to SQLAlchemy's
  `.offset()` / `.limit()`.
- An optional `status` query parameter (typed as the existing `TaskStatus`
  enum, so FastAPI rejects invalid values with `422` automatically) filters
  the query with `Task.status == status` **before** pagination is applied —
  the same filter-then-paginate order already used for `Task.user_id`.
- `total` in the response reflects the row count of the filtered query (after
  the `status` filter, if any), not the caller's total unfiltered task count.
  A caller filtering to `status=done` sees `total` as the number of done
  tasks, matching what `items` across all pages of that filter would add up
  to.

A composite index, `ix_tasks_user_id_created_at` on
`tasks(user_id, created_at)` ([migration
a315f76bfd22](../../alembic/versions/a315f76bfd22_add_composite_index_on_tasks_user_id_.py)),
backs the query. Every list query filters by `user_id` and orders by
`created_at DESC`; without a composite index covering both, Postgres can use
the existing single-column index on `user_id` to find the right rows but
still has to sort them by `created_at` as a separate step. The composite
index lets it satisfy the filter and the ordering from the same index scan,
with no separate sort.

## Consequences

**Positive**

- Simple to implement and simple for API consumers to reason about: `page`
  and `limit` are plain integers, not opaque tokens that have to be passed
  back verbatim.
- Supports jumping to an arbitrary page, which is a reasonable expectation
  for a small per-user task list rendered as a conventional paginated table.
- The composite index keeps the common case (list my tasks, newest first,
  optionally filtered by status) to a single index scan with no extra sort.

**Negative**

- `OFFSET` cost grows with page depth: Postgres still has to scan and discard
  every row before the offset, even though the composite index avoids the
  separate sort. At current per-user task volumes this is not a real cost,
  but it doesn't stay flat as a user's task count grows into the thousands.
- Offset-based pages are not stable under concurrent writes — if a task is
  inserted or deleted between two page requests, a row can be skipped or
  shown twice across pages. This is a known, accepted tradeoff at this
  project's scale, not something guarded against today.

## Future improvements

If per-user task volume grows large enough for `OFFSET` cost to become
noticeable, or if the product ever wants infinite-scroll-style UX instead of
numbered pages, cursor-based pagination (keyed on `(created_at, id)` to break
ties, using the composite index the same way) is the natural next step. It
would replace `page` with an opaque `cursor` parameter and drop the
`OFFSET`-driven page-jump behavior in exchange for stable, constant-time
pagination regardless of how deep into the list a caller scrolls.
