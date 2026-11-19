---
id: ADR-0002
title: A registry of repositories and manifest contracts for modules, plugins and providers
status: proposed
date: 2026-11-02
requirements: [SYS-0012, SYS-0040]
supersedes: []
superseded_by: []
---

# A registry of repositories and manifest contracts for modules, plugins and providers

## Context

The ecosystem is many repositories, versioned apart. The keeper must offer
applications, plugins and reusable modules without being rebuilt when one is
added, and a person must be able to ask which parts exist and whether the
checkouts agree.

## Decision

`robohub` holds the registry of the ecosystem's repositories
(`registry/modules/`), and the installed sets of plugins
(`plugins/registry.yml`), providers (`providers/registry.yml`) and reusable
modules (`modules/registry.yml`). Each part's own `module.yml` stays the truth
about what it is; a registry entry says only where it is and what it is for,
and an entry whose manifest is no longer on disk is not used. What a manifest
must say for each kind is a contract written once in `robohub`'s `module.yml`
(`plugin_registry`, `module_registry`) and checked by `robohub validate`.

## Consequences

- A new board, plugin or module is offered without changing the keeper.
- Every repository carries its version and changelog in its own manifest
  directory, and the registry repeats neither.
- The registry and the checkouts can disagree; `robohub registry check` says
  where.
