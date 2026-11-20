---
id: ADR-0019
title: Chosen readings are published outward as static snapshots by a feed application
status: accepted
date: 2026-11-20
requirements: [SYS-0071, SYS-0001, SYS-0032, SYS-0033]
supersedes: []
superseded_by: []
---

# Chosen readings are published outward as static snapshots by a feed application

## Context

The person wants readings of the installation — a temperature from Mesh, a
plug's power, a value Aquarium or Energy derives — shown on pages of other sites
by small JavaScript widgets, like RoboHub's own dashboard widgets but for
external use. Traffic is expected to be low; robustness and privacy matter more.

What exists: every application listens on loopback (SYS-0032, ADR-0016); Mesh
answers a source's value at `/mesh/api/projects/{project}/sources/{source}/value`;
Aquarium and Energy carry `appapi` (`/api/v1/values`, `/values/{id}`,
`/values/{id}/history`); an application the keeper starts may call the
applications its manifest lists under `deploy.calls`, at `RHO_SERVICE_<NAME>_URL`,
with a service token the runtime obtains for the callee's audience and a
read-only scope. The installation runs on a home machine (today WSL), which
sleeps, restarts and sits behind a home router.

The analysis of 2026-11-20 weighed three ways to reach the internet: serving
widgets from the installation through a reverse proxy and a port-forward, a
tunnel service, or pushing snapshots of the chosen values to static hosting. The
maintainer chose the last, and to leave the hosting target open (a pluggable
publisher, with only a local directory at first).

## Decision

1. **A separate application, `robohub-feed`** (its own repository), run by the
   keeper like any application, owns external publishing. Mesh, Aquarium and
   Energy do not change and nothing of theirs is exposed.
2. **It publishes outward; nothing reaches in.** On each refresh it reads the
   chosen values from the applications it calls (`deploy.calls`), with read-only
   service tokens, and writes static snapshots — one JSON file per feed — plus a
   dependency-free `widget.js`, through a publisher. External pages read only
   those files, from wherever they are hosted; they never reach the
   installation.
3. **A feed is an explicit, minimal selection**: a title, an unguessable id, a
   refresh interval, and items (a label, the source, a unit, optional history).
   A snapshot carries labels, values, units and times only — no application,
   project, node or source identifier, no address.
4. **A reading that stops is shown as stale, not hidden or faked**: each item
   carries the time of its reading, a source that cannot be read keeps its last
   value marked stale, and the widget says so.
5. **Publishers are pluggable.** A publisher takes the files of one refresh and
   puts them somewhere, atomically per file. The first is `directory` (a local
   folder — for testing, or for a folder a local web server or a sync tool
   serves). Git (e.g. GitHub Pages), SSH/rsync and S3-compatible publishers are
   added later, each a decision of its own about the credential it needs, which
   is kept owner-only and never in a snapshot (SYS-0033).
6. **The widget is one script**, a custom element (`<robohub-widget>`) that
   fetches a snapshot without credentials, renders a number, a chart or a small
   table, refreshes at the feed's interval and marks stale readings; it stores
   nothing and sets no cookies.

## Consequences

- External pages keep showing the last published values while the house is
  offline, marked stale once they age; the installation's outage is invisible
  to them otherwise.
- Nothing is opened on the home router; the applications stay on loopback.
- Values are as fresh as the refresh interval (30 s at the least) plus the
  hosting's cache — not live; a live (SSE) widget would need serving from the
  installation and is not part of this decision.
- The feed application is one more keeper application, with Phase 1's
  supervision: restarted on failure, watched, isolated.
- Until a real publisher is added, publishing reaches only a local directory.

## Alternatives considered

- **Serving widgets from the installation behind a reverse proxy and a
  port-forward** — live values, but the house is exposed, WSL needs Windows port
  forwarding, and an offline house shows nothing. Rejected for now.
- **A tunnel service** — no open port, but a cloud dependency for exposure and
  the same offline problem. Rejected for now.
- **Publishing from each application (Mesh, Aquarium, Energy)** — no new
  application, but three places to secure and to keep in step, and an
  application's admin surface next to its public output. Rejected.
