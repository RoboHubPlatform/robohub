---
id: ADR-0003
title: The keeper is the only issuer of credentials
status: proposed
date: 2026-11-04
requirements: [SYS-0006, SYS-0009, SYS-0011, SYS-0029, SYS-0030]
supersedes: []
superseded_by: []
---

# The keeper is the only issuer of credentials

## Context

Several applications need to know who a person is, and programs call each
other (an application calls Mesh, Mesh calls a gateway). A password store or a
signing key per application would multiply what must be protected and rotated,
and would sign a person in several times.

## Decision

The keeper is the one authorization server. It alone holds an ES256 (P-256)
signing key, publishes the public key at `/auth/public-key`, and signs every
credential: one-use sign-in tickets for an application's audience and callback,
valid thirty seconds; application session tokens of at most eight hours; and
service tokens for an audience and the scopes a program's client was registered
for, valid at most ten minutes. Every relying party — each application, each
gateway, the keeper itself — verifies offline with the public key, through
Rho's generated auth middleware, which also strips identity headers it did not
set. There is no static token anywhere.

## Consequences

- One key to protect and one place to rotate it; rotation stops every old
  credential at once.
- A keeper that is down signs nobody in, but sessions already open keep working
  and a keeper that cannot be reached signs nobody out.
- Applications must be kept away from the key files (see ADR-0005 and the
  keeper's isolation).
