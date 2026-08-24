# 0003. HS256 symmetric signing over RS256

## Status

Accepted

## Context

JWT supports two broad families of signing algorithms: symmetric (HMAC,
e.g. HS256) and asymmetric (public/private key, e.g. RS256). With HS256,
the same `SECRET_KEY` is used both to sign a token and to verify it — any
party that can verify a token can also forge one. With RS256, a private key
signs the token and a separate public key verifies it, so verification can
be handed out freely without exposing the ability to mint new tokens.

Looking at [app/core/security.py](../../app/core/security.py), `jwt.encode`
and `jwt.decode` both run inside Tasklane, using the same `SECRET_KEY` read
from [app/core/config.py](../../app/core/config.py). Nothing outside this
service currently needs to verify a Tasklane-issued token. There's one
service, one process boundary, and one place tokens get checked.

## Decision

Use HS256. It's the simpler of the two — one secret, symmetric HMAC, no key
pair to generate or rotate — and matches the current architecture, where
signing and verification always happen in the same place.

## Consequences

**Positive**

- One secret to manage instead of a key pair. Less operational overhead,
  easier to reason about, easier to rotate if it ever leaks (rotate one
  value, not a signing/verification pair kept in sync across services).
- Nothing to get wrong about key distribution, since nothing else needs
  the key.

**Negative**

- The signing secret and the verification secret are the same value. Any
  component that needs to verify tokens also gains the ability to forge
  them. That's fine as an internal detail of a single service, but it
  means the secret can never be handed to another service just so it can
  check tokens — doing so would let that service impersonate any user.
- If Tasklane ever needs another service to independently verify its
  tokens (an API gateway, a separate microservice, a third-party consumer)
  without trusting that service to also issue tokens, HS256 doesn't
  support that safely. RS256 would be required instead, since it lets the
  public key be distributed for verification while the private key stays
  only with the service that issues tokens.

## Future improvements

If this project evolves from a single service into a multi-service
architecture — which the README already flags as the direction for later
projects in this series — migrating from HS256 to RS256 would be the
natural next step. That would mean generating a key pair, keeping the
private key scoped to whichever service issues tokens, and distributing
only the public key to any service that just needs to verify them.
