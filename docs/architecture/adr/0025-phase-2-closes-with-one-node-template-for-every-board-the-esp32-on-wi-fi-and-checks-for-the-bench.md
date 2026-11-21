---
id: ADR-0025
title: Phase 2 closes with one node template for every board, the ESP32 on Wi-Fi, and checks for the bench
status: accepted
date: 2026-11-21
requirements: [SYS-0072, SYS-0070]
supersedes: []
superseded_by: []
---

# Phase 2 closes with one node template for every board, the ESP32 on Wi-Fi, and checks for the bench

## Context

ADR-0021 planned Phase 2 as 2a (health), 2b (the update protocol and Mesh's job),
2c (the Pico 2 W) and 2d (the ESP32). After 2d, four gaps remain between what
was built and what a mesh can use:

- **Mesh cannot build an ESP32 node.** Every node is built from one template, the
  DS18B20 telemetry example in robohub-drivers, which names robohub-pico as its
  platform and `pico2w` as its only preset. `rho build -target lolin32-lite`
  stops with "this program does not declare that it is written for it". The
  ESP32's update slot (ADR-0024) is therefore unreachable from Mesh.
- **The ESP32 has no network layer.** robohub-esp32 implements GPIO, I2C, SPI,
  UART, timers and RS-485, but not `robohub/net.h`. The board's manifest offers
  Wi-Fi, yet a node could reach its parent only over UART.
- **The Pico was checked on the board only for kept and rolled back.** An
  interrupted transfer that resumes, and a refused downgrade, are checked on the
  Linux host board alone. The whole chain — Mesh builds, flashes, then updates
  over Wi-Fi through the gateway — has never run end to end.
- **Health and the keystore have no check on the board** for the ESP32, the
  STM32 and the UNO R3 (ESP-0007, STM-0008, AVR-0011). Nor does any platform have
  a check that its keystore holds a key across a reset (RNODE-0012).

The template also cannot simply gain a second preset. A manifest's `depends`
and `c_connection.library` apply to every preset, so one manifest cannot name
robohub-pico for `pico2w` and robohub-esp32 for `lolin32-lite`.

## Decision

Decided by the maintainer on 2026-11-21: the ESP32 on Wi-Fi and UART, a
board-neutral template, check examples per platform, and on the attached
Pico 2 W the update check extended and the full chain run.

1. **rho lets a dependency belong to presets.** A `depends` entry may name
   `presets: [...]`: it is resolved as before, but a build for another preset
   leaves it out of the generated project. A `c_connection.variants.<preset>`
   may name its own `library`. A manifest that names neither builds as it did.
2. **robohub-node carries the node template** (`template/`): the core, the link,
   telemetry and the managed layer, with no sensor of its own and one preset per
   platform it supports (`pico2w`, `lolin32-lite`). Each platform is a
   dependency of its own preset. The link — Wi-Fi socket, or UART — is chosen
   by configuration. Mesh fits sensors into `sensors.c` as it does today. Board
   specifics, such as the Pico's USB console, stay behind the platform's
   console contract, so the template includes no SDK header.
3. **Mesh builds every node from that template**, for the node's board preset.
   A board the template has no preset for is refused before anything is
   prepared, saying so. The DS18B20 telemetry example goes back to being a
   driver example, and DRV-TEMP-0005 is retired.
4. **The ESP32 implements `robohub/net.h`** on ESP-IDF: a Wi-Fi station and TCP
   sockets through lwIP. Joining a network takes as long as it takes, so the
   join is polled with the watchdog fed, as on the Pico.
5. **Each platform has a health check on the board.** An example, like the
   Pico's `health_check`, walks through the health contracts and the keystore
   — a key stored, the board reset, the same key loaded, a second key stored
   and loaded — and prints `passed`. Each is built in CI and declared skipped
   until a board is on the bench. The Pico's gains the keystore steps and is
   run on the attached board.
6. **The Pico's update check covers the rest**: a transfer cut halfway that
   resumes where the board says, and a downgrade the board refuses. It runs on
   the attached board. Then the full chain runs once: Mesh builds and flashes the
   Pico 2 W as a node, then updates it over Wi-Fi through the gateway. That run
   is the reflash Phase 2c left owed.

## Consequences

- rho 0.21.0: `depends[].presets` and `c_connection.variants.<preset>.library`,
  read by rho-deps and by the C project generator, with tests.
- robohub-node gains `template/` (RNODE-TPL-0001..0003).
- robohub-esp32 gains `esp_net.c` (ESP-0010) and a health check (ESP-0011).
- robohub-stm32 (STM-0009) and robohub-avr (AVR-0012) gain health checks. The
  UNO R3 has no core, so its check calls the contracts directly.
- robohub-pico: PICO-0013 (the update check resumes and refuses) and PICO-0014
  (the health check holds a key across a reset).
- robohub-mesh: MESH-0043 (every node from robohub-node's template), and an
  on-target suite for the full chain. MESH-0044, added at approval: a gateway on
  Mesh's host under WSL2 in NAT mode is checked for the Windows port forward that
  boards on the LAN need, and Mesh shows the commands when it is missing.
- robohub-drivers: the example drops the node layers it carried for Mesh.
  DRV-TEMP-0005 is retired.
- With this, ESP32 nodes are built, flashed and updated by Mesh like Pico ones.
  STM32 updates still wait for MCUboot with the Zephyr adapter (Phase 3).

## Alternatives considered

- **Mesh writes the platform into each prepared copy** — no rho change, but
  the template could not be built, tested or published on its own, and Mesh
  would keep a second description of each platform. Rejected.
- **A template per platform** — simple, but every change to the node would be
  made twice, and the two would drift. Rejected.
- **Extending the DS18B20 example** — less moving, but a driver repository
  would keep owning the firmware for every node, with a sensor the ESP32 cannot
  read. Rejected.
- **UART only for the ESP32** — smaller, but the board offers Wi-Fi in Mesh and
  could not use it. Rejected.
