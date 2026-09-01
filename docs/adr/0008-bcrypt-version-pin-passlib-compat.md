# 0008. bcrypt pinned to 4.0.1 for passlib compatibility

## Status

Accepted

## Context

[ADR 0004](0004-bcrypt-password-hashing.md) chose bcrypt as the password
hashing scheme, used through passlib's `CryptContext`
([app/core/security.py:6](../../app/core/security.py#L6)). Passlib 1.7.4 —
the version pinned in [requirements.txt](../../requirements.txt) —
detects the installed bcrypt backend's version by reading
`bcrypt.__about__.__version__`. Starting with bcrypt 4.1, that module
attribute was removed as part of a broader move away from the legacy
`__about__` metadata pattern, which passlib's version probe was never
updated to expect. Any bcrypt version from 4.1 onward breaks passlib's
version detection.

This was found the hard way: an unrelated `pip install` run locally
upgraded bcrypt past 4.0.1 without that being a deliberate decision, and it
went unnoticed until this review.

## Decision

Pin `bcrypt==4.0.1` in requirements.txt — the last release before the
`__about__` attribute was removed — instead of tracking the latest bcrypt
release.

## Consequences

**Positive**

- passlib's `CryptContext` hashing and verification keep working without
  warnings or errors; no need to patch passlib or work around its version
  probe.
- The pin is explicit and self-documenting in requirements.txt, instead of
  relying on whatever bcrypt version happens to already be installed in a
  given environment.

**Negative**

- Tasklane is intentionally held back from newer bcrypt releases — bug
  fixes and potential security patches included — for as long as this
  passlib version is in use.
- The pin is easy to lose silently, which is exactly what happened here:
  a later, unrelated `pip install` bumped the installed bcrypt past 4.0.1
  without anyone deciding that on purpose. `pip install -r requirements.txt`
  respects the pin, but nothing currently guards against a subsequent ad
  hoc install drifting the environment away from it.

## Future improvements

- Revisit this once passlib ships a release with an updated bcrypt version
  probe, or if Tasklane moves off passlib directly onto the `bcrypt`
  package's own API, sidestepping the version-detection issue at the
  source.
- A CI step that fails when the installed `bcrypt` version doesn't match
  what's pinned in requirements.txt would catch a silent drift like this
  one before it merges, instead of relying on someone noticing it during
  an unrelated review.
