---
id: ADR-0014
title: RoboHub is licensed under MIT
status: proposed
date: 2026-10-21
requirements: [SYS-0040]
supersedes: []
superseded_by: []
---

# RoboHub is licensed under MIT

## Context

RoboHub's repositories are public, and its modules are meant to be included
in other people's applications and firmware, including firmware shipped on
devices.

## Decision

Every RoboHub repository is licensed under the MIT licence, named in its
`LICENSE` file and its `module.yml`, and each Rho source carries
`SPDX-License-Identifier: MIT` in its header. The Rho toolchain has its own
licence, decided in its own repository.

## Consequences

- Anyone may use, change and ship the code, with the notice kept.
- A contribution is accepted under the same licence.
- A licence change alone is not a release-worthy change and does not bump a
  version.
