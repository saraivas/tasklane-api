# 0006. 404 instead of 403 when a task belongs to another user

## Status

Accepted

## Context

Every task-scoped route in
[app/routers/tasks.py](../../app/routers/tasks.py) — `GET /tasks/{id}`,
`PATCH /tasks/{id}`, `DELETE /tasks/{id}` — looks up the task with both the
task id and the authenticated user's id in the same query condition:
`Task.id == task_id, Task.user_id == current_user.id`. When a task exists
but belongs to a different user, that query returns nothing, and the route
responds exactly as it would if the task id didn't exist at all:
`404 Not Found`.

REST convention offers two candidate status codes for "you can't do that to
this resource": `403 Forbidden` (the resource exists, you're just not
allowed to touch it) and `404 Not Found`. `403` is the more literal reading
of what actually happened, but it also confirms to the caller that a task
with that id exists somewhere in the system, just gated off from them.
Confirmed in
[tests/integration/test_tasks.py](../../tests/integration/test_tasks.py):
`test_user_cannot_see_another_users_task` and
`test_user_cannot_delete_another_users_task` both assert `404`.

## Decision

Return `404` for both "task doesn't exist" and "task exists but belongs to
someone else." The two cases are deliberately made indistinguishable from
outside the service.

## Consequences

**Positive**

- Task ids never become an oracle for enumerating what exists in the
  system — probing `/tasks/{guessed-id}` reveals nothing about whether that
  id belongs to a real task owned by someone else, only that the caller
  can't access it.
- Simpler implementation: one query condition covers existence and
  ownership together, instead of a separate existence check and a separate
  ownership check that would need to return different status codes.

**Negative**

- Deviates from the more literal HTTP semantics, where `403` communicates
  "this resource exists" and `404` communicates "nothing here." A
  legitimate caller debugging their own mistake sees `404` either way, and
  can't tell "wrong id" apart from "right id, wrong owner" from the
  response alone.
- Task ids are already UUIDv4
  ([app/models/task.py:18](../../app/models/task.py#L18)), which are
  already hard to guess. The `404` choice is defense in depth layered on
  top of an ID scheme that's already resistant to enumeration, not the
  primary defense against it.
