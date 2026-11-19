---
id: ADR-0010
title: Authenticate every board frame with derived keys, sessions and key epochs
status: proposed
date: 2026-11-13
requirements: [SYS-0019, SYS-0020, SYS-0021, SYS-0022, SYS-0023, SYS-0026]
supersedes: []
superseded_by: []
---

# Authenticate every board frame with derived keys, sessions and key epochs

## Context

Boards report and take commands over serial, USB and Wi-Fi links anyone near
can reach. Readings and commands are not secret, but a forged or replayed frame
can switch a heater. Boards are small, many, and flashed by Mesh; typing keys
into them, or a public-key handshake on an AVR, is not practical.

## Decision

Each gateway has a 256-bit key; each board an id minted by Mesh; the board's
key is derived from the two (`HMAC-SHA256(K_gw, "rh-dev1" ‖ uid)[0:16]`) and
built into its firmware, so no key crosses a network. A board opens a session
with HELLO/SESSION, which derives a key per direction; every frame then carries
the session id, a counter that only rises and a 64-bit truncated HMAC tag, and
is dropped otherwise. Frames are authenticated, not encrypted. A node manifest
from Mesh says which boards a gateway admits, where they sit and which are
revoked. A key is rotated without flashing by raising the board's epoch
(`"rh-dev2" ‖ uid ‖ epoch`): the gateway sends the new key wrapped under the
current one (REKEY), the board proves it (REKEY_ACK), and from then on the old
epoch opens nothing; one epoch of grace is kept. A relay is enrolled as a board
of its parent and carries its boards' frames whole.

## Consequences

- A board built by Mesh is enrolled by being built; revocation needs no
  re-keying of the mesh.
- No forward secrecy: whoever holds an old key and recorded the REKEY frame can
  unwrap the new key; a key known stolen is also reflashed.
- A board whose platform has no key store cannot take a rotation until it is
  reflashed.
- The gateway must keep sessions and counters across a restart
  (robohub-gateway:ADR-0001, robohub-gateway:ADR-0002).
