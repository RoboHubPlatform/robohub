---
id: ADR-0004
title: Serve every application under the keeper's origin
status: superseded
date: 2026-11-14
requirements: [SYS-0005, SYS-0017, SYS-0032]
supersedes: []
superseded_by: [ADR-0016]
---

# Serve every application under the keeper's origin

## Context

Applications listened on ports of their own and were linked there. A browser
scopes cookies by host and not by port, so every application received every
other one's cookies, the keeper's admin session among them; and reaching the
installation from elsewhere needed a tunnel or a proxy per port.

## Decision

The keeper serves each application it runs at `/app/<name>/` on its own
address (`127.0.0.1:19090`), through Rho's `app_proxy` middleware, to the
application's loopback port. The keeper's own session cookie is never
forwarded; an application's cookies, links, redirects and form targets are
rewritten onto its prefix; `X-Forwarded-Prefix`, `-Host` and `-Proto` say where
it is reached; event streams pass through. An application signs in through the
same origin. `keeper.proxy_apps=off` goes back to ports.

## Consequences

- One address and one TLS proxy reach everything.
- Same-site no longer tells the keeper from an application, so every relying
  party refuses forms posted from another origin (`same_origin`).
- An application must work under a path prefix it learns at run time.
