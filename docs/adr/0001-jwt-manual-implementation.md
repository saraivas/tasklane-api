# 0001. Manual JWT implementation instead of a third-party auth provider

## Status

Accepted

## Context

Tasklane needs authentication: users register, log in, and get tokens they
use to access their own tasks. There are two broad ways to get there. One is
to hand the whole problem to a provider like Auth0, Clerk, or Supabase Auth
and consume their SDK. The other is to implement it directly with a JWT
library and own every piece: password hashing, token issuance, token
verification, refresh flow.

This project exists specifically to close a gap in backend fundamentals —
the README frames it as understanding "JWT auth from the inside out," not as
shipping a product as fast as possible. A hosted provider would solve the
immediate problem but would also hide the exact mechanics this project is
meant to teach: what actually goes into a token, how signing and expiry
work, what a refresh flow has to guard against, and where the sharp edges
are.

There's also no external constraint pushing toward a managed provider here.
Tasklane is a single-service API with no social login, no SSO, no
compliance requirement, and no multi-tenant org model — the kind of
complexity where a third-party provider starts paying for itself. None of
that applies yet.

## Decision

Implement JWT authentication manually using `python-jose` for signing and
verification, and `passlib` (bcrypt) for password hashing. See
[app/core/security.py](../../app/core/security.py).

The API issues two tokens on login: a short-lived access token (default 30
minutes, configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`) and a longer-lived
refresh token (7 days). Both are signed HS256 JWTs carrying `sub` (user id),
`exp`, and a `type` claim (`access` or `refresh`) so the two can't be
swapped for each other. Secret key and algorithm are read from environment
variables via [app/core/config.py](../../app/core/config.py), never
hardcoded.

The refresh token strategy itself — including what it deliberately does not
do yet — is documented separately in
[ADR 0002](0002-refresh-token-strategy.md).

## Consequences

**Positive**

- Full visibility into every step of the auth flow: hashing, signing,
  expiry, verification. That visibility is the point of this project.
- No external dependency, no vendor account, no network call in the
  critical path of login or token verification.
- No cost, and no data about users sitting with a third party.
- Full control over the token payload and claims, which matters for the
  next projects in this series where multi-tenancy and richer claims are
  likely.

**Negative**

- Every security property has to be built and reasoned about by hand —
  hashing algorithm choice, token expiry, refresh handling, revocation.
  A provider bakes in years of hardening; here that hardening has to be
  added deliberately, and gaps can go unnoticed until they matter (see
  ADR 0002 for a concrete example already accepted as a known gap).
- No built-in support for things a real product would eventually want —
  password reset flows, email verification, MFA, social login, breach
  detection. All of that would need to be built from scratch if this ever
  grew past a learning project.
- More code to maintain and more surface area to test than integrating an
  SDK would require.
