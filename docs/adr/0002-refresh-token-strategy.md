# 0002. Refresh token strategy: sliding expiration, no absolute cap, no reuse detection

## Status

Accepted

## Context

Following [ADR 0001](0001-jwt-manual-implementation.md), Tasklane issues its
own access and refresh tokens. `POST /auth/refresh` takes a valid refresh
token and returns a new access token. The question this ADR answers is what
happens to the refresh token itself on that call, and what protections
around it are in scope for v1.

Looking at [app/core/security.py](../../app/core/security.py),
`create_refresh_token` always issues a token with a fresh 7-day expiry from
the moment it's called. There is no second claim tracking when the user's
session originally started, and nothing recording which refresh tokens have
already been used.

## Decision

**Sliding expiration.** Every refresh token is valid for 7 days from the
moment it's issued. As long as the user (or their client) calls
`/auth/refresh` at least once every 7 days, they get a new refresh token
with another full 7-day window. In practice, an active user's session never
expires — there's no ceiling on how long it can be extended, only a floor on
how often it has to be renewed.

**No absolute expiration.** v1 does not track when the session originally
began. A `session_started_at` (or equivalent) claim that would cap the
total session lifetime regardless of activity — say, 30 days from first
login no matter how often the token is refreshed — is not implemented.

**No reuse detection.** v1 does not track which refresh tokens have already
been redeemed. If a refresh token is stolen and used by an attacker, and the
legitimate user later tries to use the same (now already-rotated) token
again, the system has no way to notice that a token which was already spent
came back. That's the standard signal that a token has been stolen, and
right now Tasklane doesn't check for it.

This is a deliberate, accepted risk for this phase of the project, not an
oversight. Tasklane is an early-stage study project — the goal right now is
to get the core JWT access/refresh mechanics working correctly and
understood end to end. Absolute expiration and reuse detection are real
security properties a production auth system needs, but adding them now
would mean building session tracking (a store for issued/used token IDs)
before the basic flow is even solid. That's the right order for a v2, not
a distraction to pull into v1.

## Consequences

**Positive**

- Simple to implement and reason about: no server-side session store, no
  extra state to keep in sync, refresh tokens are just JWTs verified
  statelessly.
- Active users are never forced to re-authenticate, which is a reasonable
  UX default for a task management app.

**Negative**

- A leaked refresh token grants effectively indefinite access as long as
  it — or any token descended from it via refresh — keeps getting used
  before expiry. There is no outer bound.
- A stolen-and-reused-old-token attack pattern would currently go
  undetected; the legitimate user and the attacker would just keep
  silently refreshing in parallel.
- Revoking a compromised session isn't possible today — there's no
  token registry to invalidate against. The only way to kill a session is
  to rotate `SECRET_KEY`, which invalidates every session for every user.

## Future improvements

- **Absolute session expiration.** Add a `session_started_at` (or
  `session_id` tied to a fixed issue time) claim set at login and carried
  through every refresh. Reject refresh requests once that original
  timestamp is older than a fixed ceiling (e.g. 30 days), independent of
  how recently the token was refreshed.
- **Refresh token reuse detection.** Track issued/redeemed refresh token
  IDs (`jti`) in a store — Redis is the natural fit given the TTL-based
  access pattern. On refresh, if the presented token's `jti` has already
  been redeemed, treat it as a signal of theft: revoke the entire token
  family for that session and force re-authentication.

Both belong to v2, once the core flow from ADR 0001 is in place and tested.
