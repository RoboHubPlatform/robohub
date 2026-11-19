---
id: ADR-0016
title: Reach every application on its own loopback port
status: accepted
date: 2026-11-19
requirements: [SYS-0005, SYS-0017, SYS-0032, SYS-0034, SYS-0063]
supersedes: [ADR-0004]
superseded_by: []
---

# Reach every application on its own loopback port

Decided by the maintainer on 2026-11-19. Supersedes {ref}`robohub:ADR-0004`.

## Context

Since {ref}`robohub:ADR-0004` the keeper served every application it runs at
`/app/<name>/` on its own address, `127.0.0.1:19090`, through Rho's generated
`app_proxy` middleware. Mesh was very slow inside the keeper
(`http://127.0.0.1:19090/app/mesh/…`) and fast on its own port
(`http://127.0.0.1:8478/mesh/p/default`).

The proxy is not the cause: it adds about 1 ms to a request and about 13 ms to a
page. The cause is the browser's limit of six HTTP/1.1 connections per origin.
Every application and the keeper shared one origin, and every page holds
long-lived event streams for as long as it is open, in every tab — Mesh's
`/mesh/faults/events` and the notifications toast stream, the keeper's own
pages, the widgets' `/widgets/events` in Aquarium and Energy. With a few tabs
open the streams hold the six connections and ordinary requests queue behind
them. On its own port an application has six connections of its own.

HTTP/2 multiplexes every request over one connection and would remove the limit,
but a browser speaks it only over TLS, and TLS on the loopback is more than the
installation should need for now. Fewer streams per page would only move the
limit.

## Decision

Applications are reached on their own loopback ports. The keeper links to each
at its own address — `http://127.0.0.1:<port><route>`, or the address the keeper
was reached at for an application its manifest opens to the network
(`deploy.listen: lan`) — from its switcher, its menu, its overview and its
**Open application** buttons, and `/api/v1/switcher` gives the port and route
rather than a path under the keeper. The keeper no longer proxies: its old
addresses, `/app/<name>/<path>?<query>`, answer with a redirect (302) to the
same path and query on the application's port, so links and bookmarks still
work; an application the keeper does not host is not found.

Shared modules keep working both ways — at a port and under a prefix behind a
proxy — and are documented for their own port.

## Consequences

- There is no single origin any more, and so no single TLS proxy or tunnel for
  reaching the installation from the network: each application is its own port,
  and one opened to the network is opened on its port.
- An application signs in on its own port: the keeper's sign-in calls it back at
  `http://127.0.0.1:<port>/auth/callback`, which the keeper already accepts.
- Cookies are per host, not per port. The browser again sends the keeper's
  session cookie (`keeper_session`, `HttpOnly`) to every application's port, as
  it did before {ref}`robohub:ADR-0004`: an application's server sees it with
  every request and must never log, forward or act on it. Only installed
  applications listen on those ports, and each is trusted code the admin
  installed; the cookie is not readable by page scripts. The keeper and the
  applications are still one site to a browser, so the `same_origin` check on
  every relying party and the form token stay. An application's own cookies are
  no longer scoped to a path under the keeper.
- A page of a hosted application is no longer on the keeper's origin, so its
  scripts cannot read the keeper's pages or the keeper's form token. The earlier
  concern that a hosted application could read the keeper's token goes away.
- Each application gets the browser's six connections to itself; the keeper's
  pages and every application's streams no longer compete.
- `keeper.proxy_apps` is gone, and nothing reads `~/.rho/keeper/proxy.txt` any
  more.
