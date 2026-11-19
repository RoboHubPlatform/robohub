---
id: ADR-0007
title: Applications reach the outside world only through named interfaces and the providers they bind
status: proposed
date: 2026-11-04
requirements: [SYS-0018, SYS-0025, SYS-0028, SYS-0036]
supersedes: []
superseded_by: []
---

# Applications reach the outside world only through named interfaces and the providers they bind

## Context

An application reads devices, publishes on MQTT and sends alerts. Calling
Mesh, a broker or an SMTP server directly would tie it to one way of doing each,
and an application could not run without the hardware or the service.

## Decision

Each outside concern is an interface in `robohub/contracts`:
`robohub.gateway` (sources, readings, history, the live feed, actions),
`robohub.bus` (MQTT topics) and `robohub.alert` (an alert on every bound
channel). Providers in `robohub/providers` implement them — Mesh and the
simulator for the gateway, MQTT for the bus, log, e-mail, Telegram and webhook
for alerts. An application lists the providers it uses under `bind:` in its
`module.yml`; only those are compiled in, and its settings change their
configuration on a running installation. The Mesh provider's `transport`
setting (`auto`, `bus`, `http`) chooses whether the live feed is followed from
the broker or from Mesh's HTTP stream, so an installation without the broker
still works.

## Consequences

- An application runs against the simulator with no mesh, and is switched
  to Mesh from its settings.
- A new channel or transport is a provider, not a change to applications.
- An interface's version is a contract: a breaking change is a major version
  that every provider and binding follows.
