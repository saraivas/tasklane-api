# 0005. PATCH instead of PUT for partial task updates

## Status

Accepted

## Context

Task updates in Tasklane are field-level: a client editing a task typically
changes one thing — flips status from `todo` to `done`, tweaks the title,
clears a description — not the whole record at once. Looking at
[app/schemas/task.py](../../app/schemas/task.py), `TaskUpdate` makes every
field `Optional` with no requirement to resend the rest, and
[app/routers/tasks.py:63-88](../../app/routers/tasks.py#L63-L88) applies
only the fields actually present in the request body via
`task_data.model_dump(exclude_unset=True)`.

HTTP gives PUT and PATCH different semantics: PUT replaces the entire
resource with the representation sent — the client is expected to send the
full resource, and anything omitted is implicitly reset — while PATCH
applies a partial modification, changing only what's included in the
request.

## Decision

Use PATCH (`@router.patch("/{task_id}")`) for task updates, not PUT.
Combined with `exclude_unset=True`, a request body only needs to contain
the fields being changed; every other field on the task is left untouched.
Pydantic v2's `exclude_unset` tracks which fields were actually present in
the incoming JSON, so `{"description": null}` (explicitly clearing the
description) and omitting `description` entirely are treated differently —
the former sets it to `None`, the latter leaves whatever value the task
already has.

## Consequences

**Positive**

- Matches how clients actually want to update a task — most edits touch
  one field, and callers don't have to fetch the current representation
  first just to resend the parts they're not changing.
- No ambiguity between "not sent" and "explicitly cleared": `exclude_unset`
  makes that distinction meaningful and lets the update apply correctly
  either way.

**Negative**

- PATCH doesn't carry PUT's spec-level guarantee of idempotency. In
  practice, repeating this endpoint's PATCH calls with the same body does
  produce the same result, but that's a property of this implementation,
  not something guaranteed by choosing PATCH in general.
- `TaskUpdate` mirrors `TaskCreate`'s fields as a separate schema, so
  validation added to one doesn't automatically apply to the other. The
  blank-title check on `TaskCreate`
  ([app/schemas/task.py:12-17](../../app/schemas/task.py#L12-L17)) is now
  duplicated on `TaskUpdate` as well (skipping the check when `title` is
  omitted, since `None` means "not being changed" under `exclude_unset`).
  Any future validation added to one schema still needs to be applied to
  the other by hand.
