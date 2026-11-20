---
id: ADR-0022
title: Firmware goes to a board over its link as an Ed25519-signed manifest and a windowed transfer, confirmed once the board is healthy
status: accepted
date: 2026-11-20
requirements: [SYS-0072, SYS-0052, SYS-0033, SYS-0001]
supersedes: []
superseded_by: []
---

# Firmware goes to a board over its link as an Ed25519-signed manifest and a windowed transfer, confirmed once the board is healthy

## Context

ADR-0021 decided the lifecycle: each chip's own A/B mechanism behind one slot
interface, health first (2a, done), updates signed with a key of their own per
mesh, the Pico 2 W first (2c) and the ESP32 next (2d). This is 2b: the update
protocol and Mesh's job, end to end against a host board, before any chip's
slots are touched.

What constrains it:

- A link frame is at most 256 bytes (`RH_TRANSPORT_MAX_FRAME_SIZE`); sealing
  costs 14 of them. A chunk carries 192 bytes of image — 1 MB is about 5 500
  chunks, a minute and a half to two minutes over a 115 200-baud UART.
- Every frame is already authenticated hop by hop by the link's sealing, and a
  relay carries a board's sealed frames whole (RELAYED), so what the master
  gateway sends reaches the board unchanged.
- The board must be able to tell where an image came from without trusting the
  gateway: a gateway that was taken over must not be able to push firmware.
- A board must never be left without an image that runs.

## Decision

Decided by the maintainer on 2026-11-20 (signature, confirmation and transfer);
the rest follows from ADR-0021.

1. **An update manifest, signed with Ed25519.** Mesh describes each update in a
   manifest — the update's id, the board's uid, the firmware version, the
   security version, the image size and SHA-256, the chunk size — and signs it
   with the mesh's update key (Ed25519, one per mesh, apart from the secure-boot
   key, owner-only on the installation's machine). The public half is compiled
   into every firmware Mesh builds for that mesh; a board without one is not
   updatable over the link and says so.
2. **Four messages** in the one wire protocol (PROTO-0008): `UPDATE_OFFER`
   (the manifest and its signature), `UPDATE_CHUNK` (an index and up to the
   chunk size of image), `UPDATE_STATUS` (the board's answer: accepted with the
   next index it expects, refused with a reason, verified, confirmed, rolled
   back) and `UPDATE_CANCEL`. All sealed, all addressed to one board.
3. **The board decides.** It refuses an offer whose signature does not verify
   under its compiled-in key, that names another board, whose security version is
   below the one it holds (no downgrade), whose image does not fit its inactive
   slot, or that arrives while another update is under way.
4. **A window of four chunks.** The sender keeps up to four chunks in flight; the
   board writes them in order to the inactive slot, hashing as it goes, and
   acknowledges with the next index it expects. A gap, a lost frame or a lost
   link resumes from that index. A board that resets during a transfer starts the
   next offer from chunk 0: its partial slot is not trusted across a reset.
5. **Verify, then boot once.** With the last chunk the board checks the SHA-256
   against the manifest, says `verified`, and asks its platform to boot the new
   slot once. The running slot is never written.
6. **Confirm when healthy.** The new image is confirmed — kept, and its security
   version made the board's — once its link session is up again and its loop has
   run 30 s with every task on time (the 2a watchdog policy). Unconfirmed, the
   next reset brings the old image back, and the board reports `rolled back`
   when it is up again.
7. **The gateway drives, Mesh decides.** Mesh builds the image, writes and signs
   the manifest, and hands both to the board's gateway; the gateway keeps the
   image, runs the window, and shows progress in its API; Mesh shows the job and
   records the deployed signature when the board confirms, as it does after a
   flash.
8. **A host board first.** robohub-linux implements the slot contract with two
   image files, so the whole path — Mesh, gateway, relay, the board's managed
   layer — is tested end to end on a host before 2c touches the RP2350.

## Consequences

- New: the slot contract in robohub-common (COMM-0013); the managed layer in
  robohub-node (RNODE-UPD-*, its ADR-0003), with a vendored Ed25519 verifier;
  the messages (PROTO-0008); the Linux slot (LNX-0009); the gateway's update
  relay (GW-0016); Mesh's update key and job (MESH-0039, MESH-0040).
- A board updated over the link keeps its secure boot: on a production board the
  image is the one signed for its ROM, and the manifest is checked on top.
- The update key is a second key to keep per mesh. Rotating it means a flash or
  an update signed with the old key that carries the new public key.
- Boards with no second image (the UNO R3) and platforms whose slot comes later
  (STM32 with Zephyr) answer `refused: not updatable`, and Mesh offers them a
  flash instead.

## Alternatives considered

- **ECDSA P-256** — common, accelerated on some parts, but a larger and slower
  software verifier where it is not, and easier to get subtly wrong. Rejected.
- **HMAC with a per-board key** — no public-key code on the board, but Mesh and
  every board would share a secret, so a key read off one board could sign for
  it. Rejected.
- **Stop-and-wait** — the simplest transfer, about twice as slow over a UART and
  worse through a relay chain. Rejected for a window of four.
- **Confirm on the first acknowledged reading** — a stronger end-to-end check,
  but a new acknowledgement message, and no use on a board that only acts.
  Rejected; session plus 30 s healthy instead.
- **Resume across a board reset** — saves a re-send after a reset mid-transfer,
  but needs the partial slot re-read and re-hashed and its state kept durably.
  Not now: a reset mid-transfer is rare and a transfer is minutes.
