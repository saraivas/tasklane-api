# 0004. bcrypt for password hashing over argon2

## Status

Accepted

## Context

Looking at [app/core/security.py](../../app/core/security.py), password
hashing goes through `passlib`'s `CryptContext`, configured with
`schemes=["bcrypt"]`. Passlib itself is hash-agnostic — it supports bcrypt,
argon2, scrypt, and others behind the same interface, and switching schemes
is mostly a one-line change plus a migration path for existing hashes
(`deprecated="auto"` already sets that up).

argon2 is the algorithm OWASP has recommended as the default choice for new
applications in recent years, largely because it was purpose-built to
resist GPU and ASIC-based cracking better than bcrypt. bcrypt predates that
recommendation by a couple of decades, but it's still considered
cryptographically sound, is what most tutorials, courses, and other
learning material use, and remains an accepted industry-standard choice —
it just isn't the current state of the art.

## Decision

Use bcrypt. It's the more established and more widely documented of the
two, which matters for a project explicitly built around learning auth
fundamentals from first principles — bcrypt's behavior and failure modes are
easier to find written up, reason about, and compare against. It's also
still considered secure for this use case; there's no known practical break
of bcrypt used correctly, just a newer alternative with a better security
margin.

## Consequences

**Positive**

- Well understood, extensively documented, and battle-tested — a
  reasonable default while the focus of this project is elsewhere (the JWT
  flow itself, per [ADR 0001](0001-jwt-manual-implementation.md)).
- Because passlib is already the abstraction in use, this isn't a
  one-way door — switching the scheme later doesn't mean touching the rest
  of the codebase.

**Negative**

- argon2 offers stronger resistance to GPU-based and hardware-accelerated
  cracking attempts than bcrypt, by design — that's the specific problem
  it was created to address. bcrypt's cost factor helps, but argon2's
  memory-hardness is a real advantage against an attacker with parallel
  hardware.
- Choosing bcrypt today means Tasklane isn't following the current OWASP
  default recommendation, even though it remains an accepted choice.

## Future improvements

Revisit this once the core auth flow is stable. Moving to argon2 would be a
low-risk change given passlib already abstracts the scheme — add
`argon2-cffi` as a dependency, add `"argon2"` to the `CryptContext` schemes
list ahead of `"bcrypt"`, and let `deprecated="auto"` rehash existing
passwords into argon2 the next time each user logs in.
