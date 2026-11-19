---
id: ADR-0001
title: Keep the simulation's state in files in the application's workspace
status: proposed
date: 2026-11-13
requirements: [SIM-0001, SIM-0009]
supersedes: []
superseded_by: []
---

# Keep the simulation's state in files in the application's workspace

## Context

The simulator is a provider of the `robohub.gateway` interface
({ref}`robohub:ADR-0007`): an application imports it and binds it beside the
Mesh provider, rather than including it as a module. An included module gets its
tables generated into the application's database by rho-sql; an imported
provider does not, and must not reach into tables it does not own. Yet the
simulation has state that outlives a request — the sources the presets
declared, each source's current value, a week of history and the feeds it
writes to — and a request (an action) and the background loop (a tick) both
change it.

## Decision

The simulator keeps its state in plain files under `data/simulator/` in the
application's workspace (`app_workspace()`): `sources.txt` and `devices.txt`
from the presets, `values.txt` with each value in thousandths, `last.txt` with
the time of the last tick, `history/<source>.txt` with one `time value` line per
point, and `follow.txt` with the feeds to write to. A tick and an action hold
the runtime's named lock `simulator` while they change `values.txt`.

## Consequences

Two applications started by hand do not share a simulation, and an application
that unbinds the simulator keeps no tables it does not use. The files are read
whole on each call, which is fine for the tens of sources a preset declares and
would not be for thousands. History older than seven days is pruned about once
an hour. A test can read and adjust the simulation's state directly, which the
smoke test does to make a probe warm quickly.
