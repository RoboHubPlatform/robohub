---
id: ADR-0021
title: A node's lifecycle uses each chip's own A/B update, health comes first, and updates are signed with a key of their own
status: accepted
date: 2026-11-20
requirements: [SYS-0072, SYS-0070, SYS-0001, SYS-0033, SYS-0052]
supersedes: []
superseded_by: []
---

# A node's lifecycle uses each chip's own A/B update, health comes first, and updates are signed with a key of their own

## Context

robohub ADR-0020 plans robohub-node's Phase 2 as the lifecycle from the edge:
health on the board, keys that survive, signed firmware updates over the link
with rollback (RNODE-0008, RNODE-0012). The analysis
(`robohub-node-phase2-analysis.html`, 2026-11-20) found:

- **Keys are mostly done.** robohub-common's keystore contract (two A/B slots
  with a sequence and a CRC) is implemented on Pico, ESP32, STM32, UNO R3 and
  Linux.
- **Production boards already use their chip's secure boot.** Pico 2 W: the image
  signed for RP2350 secure boot (secp256k1, the key's hash in OTP); ESP32: Secure
  Boot v2 (RSA-3072) with a production partition table. Mesh keeps one signing-key
  path per mesh for it.
- **The chips that can hold two images can also choose between them.** The RP2350
  boot ROM reads a partition table with an A/B pair and boots a new image once
  ("try before you buy"), keeping it only when the application confirms it.
  ESP-IDF has two OTA app slots and, with a bootloader built for it, rollback of an
  image the application does not confirm. STM32 boards differ (dual-bank swap on
  many); MCUboot (swap with a test image and revert) is at home in Zephyr. The UNO
  R3's 32 KB hold one image and a serial bootloader.
- **No RoboHub interface offers a watchdog, a reset reason or a fault record**, and
  the wire protocol has no message that pushes a board's health.

## Decision

Decided by the maintainer on 2026-11-20:

1. **Each chip's own A/B mechanism, behind one slot interface** in
   robohub-common (write the inactive slot, verify it, boot it once, confirm or
   fall back): the RP2350 boot ROM's partitions and TBYB, ESP-IDF's OTA slots with
   rollback. The secure boot production boards already use keeps verifying what
   boots. **STM32 gets MCUboot with the Zephyr adapter** (Phase 3).
2. **Health first.** Sub-phase 2a — a watchdog contract, a portable reset reason
   and a fault record in robohub-common, their implementations on every board
   platform, the core's watchdog policy, and the report — comes before any update
   work. 2b is the update protocol and Mesh's update job; 2c the Pico 2 W; 2d the
   ESP32.
3. **Updates are signed with a key of their own**, one per mesh, apart from the
   mesh's secure-boot key: Mesh signs each update's manifest with it, and a board
   accepts an update only under it. A stolen update key cannot make an image a
   production board's ROM will boot; a stolen secure-boot key cannot push an
   update. Both stay owner-only on the installation's machine (SYS-0033).
4. **The first board updated over the link is the Pico 2 W** already in the
   default mesh.
5. **The UNO R3 gets health only**; its firmware stays a flash from Mesh.
6. **Health travels in a new wire message, `HEALTH`**, pushed by a board once per
   boot when its session is up (and answered again on request): the reset reason,
   the boot count and the last fault record. It is an addition to the one wire
   protocol (SYS-0052); HELLO does not change.

## Consequences

- 2a touches robohub-common (contracts), robohub-pico, -esp32, -stm32 and -avr
  (implementations), robohub-node (the core's policy), robohub's protocol
  (`HEALTH`), robohub-gateway (receiving and keeping it) and robohub-mesh
  (showing it, alerting on a watchdog or fault reset).
- 2b adds the update key to Mesh beside the secure-boot key, an update manifest
  format, and the update messages; the gateway relays them.
- A production board keeps both checks: its ROM's on the image, the runtime's on
  the manifest.
- The UNO R3 and boards without a second image are reported as not updatable over
  the link, rather than failing an update.

## Alternatives considered

- **MCUboot everywhere** — one format and one tool, but on RP2350 and ESP32 it
  would sit behind the ROM's own secure boot: two keys and two formats for one
  image. Rejected for those; chosen for STM32.
- **A bootloader of RoboHub's own** — the hardest code to get right, duplicating
  what the chips already do. Rejected.
- **Updates before health** — the visible feature first, but an update's
  confirmation needs the watchdog to roll a hanging image back. Rejected.
- **One key for secure boot and updates** — one key to keep, but one theft
  compromises both. Rejected by the maintainer.
- **Health as SensorReading fields** — no protocol change, but a fault record is
  several fields read once, not a measurement, and it would mix with readings.
  Rejected.
