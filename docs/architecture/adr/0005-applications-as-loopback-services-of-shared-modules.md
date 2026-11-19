---
id: ADR-0005
title: An application is one loopback HTTP service, built mostly from shared modules
status: proposed
date: 2026-11-02
requirements: [SYS-0013, SYS-0031, SYS-0032]
supersedes: []
superseded_by: []
---

# An application is one loopback HTTP service, built mostly from shared modules

## Context

Mesh, the aquarium and energy each need a shell, settings, inventory, a
scheduler, rules, a journal, dashboard widgets, forms, languages and logging.
Written per application they would drift apart; run as separate services they
would need ports, sign-in and supervision of their own.

## Decision

An application is one HTTP service on one port, listening on `127.0.0.1`
unless its manifest says `deploy.listen: lan`, run by the keeper as a systemd
user unit. It is mostly shared modules from `robohub/modules`: a module has no
port or process of its own, it registers its routes on the including
application's router, and it asks the application for what differs through
`host_*` functions the application defines (`host_shell`, `host_app`,
`host_devices_*`, …). Machinery is shared; definitions — rules, presets,
categories — belong to each application.

## Consequences

- A fix in a shared module reaches every application on its next build.
- A module's version moves independently of the applications that include it,
  and an application states the versions it needs.
- A module cannot run alone; it is tested through a host.
