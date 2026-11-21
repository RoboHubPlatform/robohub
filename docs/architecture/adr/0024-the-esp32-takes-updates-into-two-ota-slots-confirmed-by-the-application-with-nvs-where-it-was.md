---
id: ADR-0024
title: The ESP32 takes updates into two OTA slots, confirmed by the application, with NVS where it was
status: accepted
date: 2026-11-20
requirements: [SYS-0072, SYS-0070]
supersedes: []
superseded_by: []
---

# The ESP32 takes updates into two OTA slots, confirmed by the application, with NVS where it was

## Context

ADR-0021 chose each chip's own A/B mechanism behind one slot interface, with the
ESP32 after the Pico 2 W; ADR-0022 fixed the protocol and the managed layer;
ADR-0023 did the RP2350. This is 2d: the ESP32 (the LOLIN32 Lite, 4 MB flash).

What ESP-IDF 6.2 (vendored) gives:

- **OTA slots**: `ota_0` and `ota_1` app partitions and an `otadata` partition
  that says which boots; `esp_ota_begin/write/end` writes and validates an image
  into the slot not running, `esp_ota_set_boot_partition` names it for the next
  boot.
- **Application rollback** (`CONFIG_BOOTLOADER_APP_ROLLBACK`): a new image boots
  as `PENDING_VERIFY`; if it is not confirmed before the next reset the
  bootloader marks it `ABORTED` and boots the previous one.
  `esp_ota_mark_app_valid_cancel_rollback()` confirms it,
  `esp_ota_mark_app_invalid_rollback_and_reboot()` gives it up, and
  `esp_ota_get_last_invalid_partition()` says one was given up.
- **6.2 turns rollback on by default with confirmation at startup**
  (`CONFIRM_ON_STARTUP`, migration guide 6.2) — an image that merely starts is
  kept. Confirmation by the application (`CONFIRM_BY_APP`) is what ADR-0022's
  "kept once healthy" needs.
- Today's builds use ESP-IDF's single-app table: NVS (24 kB, which holds the
  keystore) at `0x9000`, then one 1 MB app. ESP-IDF's `two_ota_large` table keeps
  NVS exactly there.

## Decision

Decided by the maintainer on 2026-11-20 (layout, migration, production, the
board check later); the rest follows from ESP-IDF and ADR-0022.

1. **Two 1700 kB OTA slots, NVS where it was.** ESP-IDF's `two_ota_large` layout:
   NVS unchanged at `0x9000` (24 kB) — so a board's rotated key survives the move —
   then `otadata`, `phy_init`, `ota_0` and `ota_1` of 1700 kB each. No factory
   app: a rollback goes to the last good image.
2. **Confirmed by the application.** Development builds set
   `CONFIG_BOOTLOADER_APP_ROLLBACK_CONFIRM_BY_APP`; the managed layer confirms
   after 30 s healthy with the session up (ADR-0022, 6), and gives up after five
   minutes (RNODE-UPD-0008). A hang is ended by the core's watchdog (the task
   watchdog, 2a), and the bootloader rolls back on the reset that follows.
3. **The update's record in NVS.** The update's id and versions, its outcome and
   the board's security version are kept in NVS beside the keystore, so the old
   image reports `rolled back` after any reset. The secure-version eFuse waits
   for production boards.
4. **The next USB flash moves a board.** From 2d, "Build and flash" for an ESP32
   writes the two-slot table and the image into `ota_0` (with `otadata` erased, so
   `ota_0` boots); Mesh records it and offers updates only after that, and only
   for firmware that carries the managed layer.
5. **Production boards stay flash-only for now.** Their table (secure boot,
   encrypted NVS) keeps its single app until secure boot, flash encryption and
   OTA are combined deliberately.
6. **The board check comes when the board does.** Everything that needs no board
   is implemented and tested in 2d; the on-board check is declared and run once
   the LOLIN32 Lite is attached.

## Consequences

- robohub-esp32 implements the slot (ESP-0008) and builds the layout and both
  images (ESP-0009); Mesh flashes ESP32 boards for OTA and offers them updates
  (MESH-0042).
- An ESP32 application has 1700 kB instead of the single-app 1 MB — more, not
  less, since the single-app table left most of the flash unused.
- Mesh offers an ESP32 an update only when its firmware carries the managed
  layer; today no driver example for the LOLIN32 Lite does, so until one does the
  board is offered flashes.

## Alternatives considered

- **A factory app and two 1 MB slots** — a recovery image always there, but NVS
  shrinks to 16 kB (the keystore would have to be written again) and each app
  gets 1 MB. Rejected.
- **Confirmation at startup** (6.2's default) — an image that starts and then
  hangs or cannot reach its gateway would be kept. Rejected.
- **OTA for production boards now** — more reach, but a mistake in combining
  secure boot, flash encryption and OTA can brick a production board. Later.
