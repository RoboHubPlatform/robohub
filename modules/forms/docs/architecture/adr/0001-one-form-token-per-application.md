---
id: ADR-0001
title: One form token per application, kept in its workspace
status: proposed
date: 2026-11-13
requirements: [FORMS-0005, FORMS-0006, SYS-0034]
supersedes: []
superseded_by: []
---

# One form token per application, kept in its workspace

## Context

Every RoboHub application is served under the keeper's origin
({ref}`robohub:ADR-0004`), so a `SameSite` cookie does not tell one
application's page from another's, and a page on any other site can still make
the person's browser post a form. Each module that draws a form needs a check
it can make before acting on a post, without a session store of its own: the
applications are stateless loopback services ({ref}`robohub:ADR-0005`) that
learn who the person is from the keeper's ticket. An earlier token, built from
the workspace path and a timestamp, could be worked out by anyone who knew the
installation.

## Decision

The forms engine keeps one synchronizer token per application: 256 bits from
the runtime's random source, written as 64 hexadecimal characters, made on first
use and kept owner-only in `<workspace>/data/csrf.txt`. Every form the engine
draws carries it in a hidden `csrf` field, a hand-drawn form adds it with
`forms_csrf_field()`, and the module that handles the post calls
`forms_csrf_ok(body)` before acting, which compares every character whatever the
first difference. A stored token that is not 64 hexadecimal characters is
replaced; when no random value can be had the token is empty and every post is
refused.

## Consequences

No session table and no per-request state are needed, and every module checks
posts the same way. The token is the same for every person and every page of
an application, so it protects against a forged cross-site post, not against
someone who can already read the application's pages; it changes only when the
file is removed. Each handler must remember to call `forms_csrf_ok` — the engine
cannot do it for them — and a program that posts to an API route carries the
keeper's token instead of the form token.
