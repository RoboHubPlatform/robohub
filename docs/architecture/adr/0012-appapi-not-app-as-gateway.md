---
id: ADR-0012
title: Applications pass on what they derive through a read-only appapi, not as gateways
status: proposed
date: 2026-11-13
requirements: [SYS-0001]
supersedes: []
superseded_by: []
---

# Applications pass on what they derive through a read-only appapi, not as gateways

## Context

The aquarium and energy derive values from readings — days since a water
change, a site's balance — that other applications and clients want. One option
was for an application to be a gateway of a mesh, with an outbox, projects and
actions; energy had been one.

## Decision

An application is not a gateway. Each offers the same small read-only REST
API through the shared `appapi` module: the values it derives and computes and
the readings it chooses to pass on, each with its history, and its journal. It
has no projects, devices or actions. Energy stopped being a Mesh gateway and
outbox.

## Consequences

- Mesh stays the only owner of telemetry (ADR-0008).
- Every application's API has the same shape.
- A client that wants to change something does it through the application's
  pages or through Mesh, not through appapi.
