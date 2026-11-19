---
id: ADR-0006
title: Each application keeps its own SQL database in its workspace
status: proposed
date: 2026-11-02
requirements: [SYS-0016, SYS-0031]
supersedes: []
superseded_by: []
---

# Each application keeps its own SQL database in its workspace

## Context

Shared modules keep records — inventory items, chores, journal entries. If a
module kept them beside itself, two applications including it would share them,
and an application's data would live in several places.

## Decision

An application owns one SQL database (SQLite, through rho-sql), in its
workspace (`~/.rho/keeper/workspaces/<name>`). The modules it includes declare
their own tables and statements and keep them in that database; a module's
settings are the `config:` the host gives it. No application opens another's
database — what one needs from another it asks over HTTP (Mesh's API, an
application's appapi).

## Consequences

- Two applications using the inventory do not share stock.
- Backing up or removing an application is one folder; uninstalling keeps it.
- A module's schema changes are migrations inside every host's database.
