---
id: ADR-0015
title: Requirements, decisions and their trace are files in each repository, checked by rho req
status: proposed
date: 2026-11-19
requirements: [SYS-0041]
supersedes: []
superseded_by: []
---

# Requirements, decisions and their trace are files in each repository, checked by rho req

## Context

Why a piece of code exists and how anyone knows it works lived in changelogs
and in the maintainer's memory. With public repositories and contributors, the
answer has to be written down, linked, and checkable in CI, and approval has to
stay with the maintainer.

## Decision

Each repository keeps requirements in `docs/requirements/**/*.yml` and
architecture decisions in `docs/architecture/adr/NNNN-slug.md`; the pages a
reader browses live in `docs/doc/`. Levels (SYS, NODE, SUB, UNIT) are declared
once in `robohub/docs/requirements/levels.yml`; SYS requirements live in
`robohub`, and each repository names its prefix and parent in its `module.yml`.
Code is tagged `@req`, tests `@verifies`. `rho req` checks the files and links,
traces requirements to test results, and numbers new entries; the keeper's
Developer section shows and edits the same. Only a maintainer named in
`MAINTAINERS.yml` approves a requirement or accepts a decision, held by a
protected `main` and CODEOWNERS, with `rho req check --base` as a guard.

## Consequences

- Every feature starts with a requirement and ends with a tagged test; a
  release waits until its approved requirements are verified.
- Existing behaviour is backfilled as proposed requirements for the maintainer
  to approve.
- Documentation moved under `docs/doc/` so that `docs/requirements/` and
  `docs/architecture/` hold only the process's files.
