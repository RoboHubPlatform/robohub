---
id: ADR-0008
title: Mesh is the only owner of telemetry
status: proposed
date: 2026-11-05
requirements: [SYS-0024, SYS-0025, SYS-0037]
supersedes: []
superseded_by: []
---

# Mesh is the only owner of telemetry

## Context

The aquarium and energy both read boards and devices. If each ingested from
gateways, kept a store and brokered commands, the same reading would be kept
twice, sources would be named differently, and every application would need
gateway credentials.

## Decision

Mesh alone ingests from gateways, polls HTTP devices, reads MQTT devices,
stores readings, names sources and actuators by `(gateway_id, uid, signal)`, and
brokers commands. It pulls each gateway's outbox with a token scoped to that
gateway, stores a page once by gateway and sequence, and acknowledges it. Other
applications read sources, history and the live feed and send actions through
`/mesh/api` with a service token for their project; none opens Mesh's store or
keeps a telemetry store of its own.

## Consequences

- A source keeps its history when the plan is reordered.
- Mesh is on the path of every reading; when it is down the gateways' outboxes
  hold readings until it collects them.
- Retention and roll-ups are Mesh's settings, the same for every application.
