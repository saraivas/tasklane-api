# 0010. Refresh token renewal in the request body, with an absolute session limit

## Status

Accepted. Partially supersedes [ADR 0002](0002-refresh-token-strategy.md).

## Context

[ADR 0002](0002-refresh-token-strategy.md) described the refresh strategy as
sliding expiration: each call to `POST /auth/refresh` returns a new refresh
token with a fresh 7-day window. A review of the documentation against the
code showed that the code did not do this. `/auth/refresh` returned only a new
access token, so the refresh token expired 7 days after login no matter how
the client used it. The ADR described a behaviour the code did not have.

The same review found two weaknesses in how the endpoint worked:

- The refresh token was a **query parameter** (`/auth/refresh?refresh_token=...`).
  URLs end up in server logs, proxy logs and browser history, which is the
  wrong place for a long-lived credential.
- ADR 0002 accepted "no absolute expiration" for v1, which means that with
  sliding expiry a session could be extended forever.

## Decision

1. **The refresh token travels in the JSON body** of `POST /auth/refresh`
   (`{"refresh_token": "..."}`), never in the URL. Sending it in the query
   string now returns `422`.
2. **Every successful refresh returns a new access token and a new refresh
   token.** The refresh token's expiry slides: each new one is valid for
   `REFRESH_TOKEN_EXPIRE_DAYS` (default 7) from the moment it is issued. This
   is what ADR 0002 already described.
3. **A session has an absolute limit**, `SESSION_MAX_LIFETIME_DAYS` (default
   30), counted from the original login. The login time is stored in an
   `auth_time` claim that is set at login and copied unchanged into every
   refreshed token. A refresh token's expiry is capped at
   `auth_time + SESSION_MAX_LIFETIME_DAYS`, and `/auth/refresh` rejects any
   token whose session is already past that limit. This needs no server-side
   state.
4. **The refresh endpoint checks that the user still exists**, and every
   failure (bad token, wrong type, expired session, deleted user) returns the
   same `401 Invalid or expired refresh token`, so a caller cannot tell the
   cases apart.
5. **Token responses carry `Cache-Control: no-store` and `Pragma: no-cache`**
   (login and refresh), as RFC 6749 section 5.1 requires.

## Consequences

**Positive**

- The documented behaviour and the code now match, and there are tests for
  each rule above.
- The refresh token no longer appears in URLs or logs.
- A session cannot be extended forever. This closes the largest downside
  recorded in ADR 0002.

**Negative / still not covered**

- **Refresh tokens are not single-use.** Because the API is stateless, a new
  refresh token does not invalidate the old one. Until the old token expires,
  it still works. If a refresh token is stolen, the thief and the legitimate
  user can both keep refreshing, up to the 30-day limit, and nothing detects
  it. Reuse detection needs a server-side record of issued and used token IDs
  (`jti`), for example in Redis. That remains a future improvement from
  ADR 0002.
- **No revocation.** A single session still cannot be killed. Rotating
  `SECRET_KEY` invalidates all sessions for all users.
- **Breaking change for clients of `/auth/refresh`:** the request moves from a
  query parameter to a JSON body. Refresh tokens issued before this change
  have no `auth_time` claim and are rejected, so users must log in again once.
- The 30-day default is a judgement call for this project, not a measured
  value. It is configurable through the environment.
