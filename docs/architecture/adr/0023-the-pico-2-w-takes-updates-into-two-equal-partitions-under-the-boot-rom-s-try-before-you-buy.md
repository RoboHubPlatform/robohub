---
id: ADR-0023
title: The Pico 2 W takes updates into two equal partitions under the boot ROM's try-before-you-buy
status: accepted
date: 2026-11-20
requirements: [SYS-0072, SYS-0070]
supersedes: []
superseded_by: []
---

# The Pico 2 W takes updates into two equal partitions under the boot ROM's try-before-you-buy

## Context

ADR-0021 chose each chip's own A/B mechanism behind one slot interface and the
Pico 2 W as the first board updated over the link; ADR-0022 fixed the protocol
and the managed layer, tested on a Linux host board. This is 2c: the RP2350's
slot.

What the RP2350 datasheet (RP-008373-DS-4) gives:

- **Partition tables and A/B partitions** (§5.1.2, §5.1.7): partitions in 4 kB
  sectors, bootable ones within the first 16 MB; of two valid images in an A/B
  pair the greater version boots.
- **Address translation** (§5.1.19): an image stored at any 4 kB-aligned place
  runs at `0x10000000`, so one binary serves either partition.
- **Flash update boot** (§5.1.16): a reboot naming the partition just written
  boots it whatever its version.
- **Try before you buy** (§5.1.17): an image flagged TBYB is entered under the
  watchdog, "fixed at 16.7 seconds", and must call `explicit_buy()`, or the
  board reboots into the other image; the timeout "can also be extended by
  reloading the watchdog counter". A TBYB-flagged image "requires a flash update
  boot to boot it" (SDK, `PICO_CRT0_IMAGE_TYPE_TBYB`); buying clears the flag and
  erases the first sector of the other partition.

The core already feeds the hardware watchdog only while every task keeps its
time (2a). That is exactly "extended by reloading the watchdog counter", made
conditional on health.

## Decision

Decided by the maintainer on 2026-11-20 (layout, migration, trial limit); the
rest follows from the datasheet and ADR-0022.

1. **Two equal partitions.** The partition table first (8 kB), partitions A and
   B of the same size (about 2 MB each on the Pico 2 W's 4 MB), then the update
   state sector and the keystore's two sectors as data the partitions never
   overlap.
2. **Updates are TBYB images.** An image sent over the link is built with the
   TBYB flag; an image flashed over USB is not. The update slot writes the
   partition not running and reboots with a flash update boot to its start.
3. **The trial is the core's watchdog.** The image on trial is entered under the
   boot ROM's watchdog; the core takes it over with its own period and feeds it
   only while every task keeps its time, so a hang rolls back as the ROM
   intends. After 30 s healthy with the session up (ADR-0022, 6) the managed
   layer confirms: `explicit_buy()`.
4. **A trial gives up after 5 minutes.** An image whose session never comes up is
   rejected: a normal reboot, and the boot ROM boots the other, untried image.
5. **The outcome is kept in flash.** The update's id and versions, and whether it
   was kept or rolled back, live in one 4 kB update state sector, so the old image
   can report `rolled back` after any reset, power loss included. The board's
   security version is kept there too (the OTP rollback rows wait for secure boot).
6. **The next USB flash moves a board to A/B.** From 2c, "Build and flash" for a
   Pico 2 W writes the partition table and the image into A. A board flashed
   before keeps working and is offered only flashes until it is flashed once
   more; Mesh knows which by what it flashed.

## Consequences

- robohub-common's slot contract gains `rh_update_reject()` (COMM-0014), and the
  managed layer the trial limit (RNODE-UPD-0008): neither is particular to the
  RP2350.
- robohub-pico implements the slot (PICO-0011) and builds both image kinds
  (PICO-0012); the DS18B20 telemetry example — the firmware Mesh builds for the
  Pico — chooses the managed layer when Mesh gives it an update key (DRV-TEMP-0005).
- Mesh flashes Pico 2 W boards with the partition table, builds TBYB images for
  updates, and offers updates to boards it flashed that way (MESH-0041).
- A board's application space is about 2 MB instead of 4 MB.

## Alternatives considered

- **A large A and a small recovery B** — more application space, but a rollback
  lands in a recovery image rather than the last good one, and a second firmware
  to maintain. Rejected.
- **A separate migration action** — clearer, but one more step for what the next
  ordinary flash does. Rejected.
- **Buying at once and rolling back by hand** — call `explicit_buy()` within the
  first seconds and invalidate the new image if it later proves unhealthy: works,
  but throws away the ROM's own revert and needs a flash erase from code that may
  be failing. Rejected.
- **A trial limit of 2 or 15 minutes** — too short for a slow Wi-Fi join, or too
  long out of contact. 5 minutes chosen.
