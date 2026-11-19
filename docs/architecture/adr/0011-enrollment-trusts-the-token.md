---
id: ADR-0011
title: Host enrollment trusts the token, not the node
status: proposed
date: 2026-11-14
requirements: [SYS-0027, SYS-0033]
supersedes: []
superseded_by: []
---

# Host enrollment trusts the token, not the node

## Context

A Linux host node enrolls with the keeper by posting a public key and a
one-time token. Whatever the node says about itself — its device id, its place
in a mesh — is under the control of whoever runs it.

## Decision

The token decides. `rho bootstrap token` on the keeper's machine writes a
token that names one device, a project, an area and a node, and an expiry
(fifteen minutes by default); a token without a device or an expiry is refused.
The node is recorded where its token places it, and a request naming another
placement is refused. A device already enrolled is replaced only by a token
made with `-reenroll`. Finding, checking and spending the token and writing the
record are one step under a lock, so a token presented many times at once
enrolls once. The credential is stored only as a salted hash; enrollment and
verification have call budgets per client.

## Consequences

- A stolen token is worth one enrollment of one device at one place, for
  minutes.
- The keeper's machine is where tokens are made; a person must be there (or
  have a shell there).
- A token is never put on a command line on the node; it is read from a
  file or standard input.
