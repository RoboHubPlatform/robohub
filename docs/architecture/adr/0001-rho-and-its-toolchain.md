---
id: ADR-0001
title: Write every part in Rho, built and checked by the Rho toolchain
status: proposed
date: 2026-10-21
requirements: [SYS-0001, SYS-0040]
supersedes: []
superseded_by: []
---

# Write every part in Rho, built and checked by the Rho toolchain

## Context

RoboHub has firmware on microcontrollers, a gateway on a small Linux host, and
web applications on a desktop or server. Written in three languages, the wire
format would be described three times, and each part would bring its own build,
lint, test and documentation tools, which the orchestrator would have to learn
one by one.

## Decision

Every part of RoboHub is a Rho module. The host side — the keeper, the
applications, the gateway, the orchestrator — is Rho generated into Go; the
firmware is C, with its payloads and framing generated from the same `rho
protocol` schemas the gateway is generated from, so the two ends of a link are
one description. Building, linting, testing, documenting, signing people in,
checking the machine and enrolling nodes are the toolchain's own components
(`rho build`, `rho lint`, `rho test`, `rho doc`, `rho auth`, `rho doctor`,
`rho bootstrap`); RoboHub decides what to run them over and collects what they
said, and carries no tool of its own that does the same.

## Consequences

- A schema change reaches the board and the gateway together.
- RoboHub depends on the toolchain's releases: a part may need a minimum Rho
  version, and its changelog says so.
- What Rho cannot express is a host port (Go) or platform C, kept small and in
  one place per part.
