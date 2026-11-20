---
id: ADR-0020
title: robohub-node is a node operating environment over existing kernels, kept as one collection
status: accepted
date: 2026-11-20
requirements: [SYS-0072, SYS-0001, SYS-0052]
supersedes: []
superseded_by: []
---

# robohub-node is a node operating environment over existing kernels, kept as one collection

## Context

The maintainer asked whether the ecosystem should grow an RTOS of its own, at the
crossing of embedded devices, edge gateways and APIs. The analysis
(`robohub-node-analysis.html`, 2026-11-20) found:

- **Kernels are solved.** FreeRTOS, Zephyr, Eclipse ThreadX (MIT, Eclipse
  Foundation, 2024) and NuttX own scheduling, timing, memory protection and board
  support; a kernel from scratch competes on what they spent a decade on.
- **The gap is above the kernel.** No system ties a node, its gateway and its API
  into one local-first contract: the manifest both sides read, a secure link by
  default, telemetry and commands as primitives, a lifecycle (identity, updates,
  health) run from the installation's own edge. Arm's Mbed OS, the one attempt at
  "device plus connectivity in one", reaches end of life in July 2026.
- **RoboHub already has half of that layer**: robohub-common (contracts:
  HAL, OSAL, net, keystore, device kinds), robohub-core (event bus, cooperative
  scheduler, application lifecycle, diagnostics — 877 lines of C),
  robohub-transport (framing, sealing, test vectors — 878), robohub-telemetry
  (routing, decimation — 255), robohub-freertos (the OSAL on FreeRTOS — 245),
  and robohub-devices' `runtime/device-node` and `nodes/gateway-node` (354).
- **Core, transport and telemetry are one chain**: telemetry depends on
  transport, transport on core; every consumer of the upper two takes core; they
  were changed over the same days. Part of the node runtime sits in
  robohub-devices, which is about equipment.
- **Board applications that never see a gateway exist and matter**: the Rho
  toolchain builds them today (a DS18B20 reader in Rho on the platform and driver
  alone).

## Decision

Decided by the maintainer on 2026-11-20:

1. **The niche is a node operating environment, not a kernel.** robohub-node
   is the layer that makes a board a RoboHub node — an application model and
   runtime services — over existing kernels (bare metal and FreeRTOS today,
   Zephyr when a board needs it). An executive of RoboHub's own is written only
   if a measured need appears, as one more kernel adapter.
2. **robohub-common stays separate**: contracts only, platform-agnostic,
   depending on nothing. Platforms implement it; robohub-node is a consumer of it.
3. **Services are layers an application opts into**: core (loop, timers,
   lifecycle, local signals and actions, settings, watchdog, diagnostics); link;
   telemetry; device node; managed lifecycle; kernel adapters. The core depends on
   nothing above it, so a board application may use no runtime, the core alone, or
   everything, and joining an installation is choosing services, not rewriting
   code (SYS-0072).
4. **One collection.** robohub-node is one repository holding these as nested
   modules. In Phase 1 robohub-core, robohub-transport, robohub-telemetry and
   robohub-freertos move in with their history, and `runtime/device-node` moves
   from robohub-devices (`nodes/gateway-node`, a node application built on
   devices' drivers, stays there: moving it would make the collection depend on
   robohub-devices); module names and ids stay, so
   consumers change only their paths; the old repositories are archived with a
   pointer.
5. **Phases**: 0 — the model (requirements, the node's ADR, the gap list; no
   code); 1 — the collection; 2 — the lifecycle from the edge (signed A/B updates,
   reset records, watchdog, per-MCU keystore); 3 — a real node and a third kernel;
   4 — an own executive only if measured.

6. **The first real node is the settlement's temperature and humidity sensor**,
   end to end: the board, its mesh at the settlement, robohub-feed, and the widget
   on the settlement's site (morlaca.ro) — decided 2026-11-20.
7. **The third kernel is Zephyr**, after bare metal and FreeRTOS; whether its
   adapter sits in the collection or beside it is decided when it is written —
   decided 2026-11-20.

## Consequences

- One pull request and one CI run cover a change across the runtime's layers;
  each module keeps its own version, CHANGELOG and requirements prefix (CORE,
  TRAN, TELE, RTOS), and the collection's version names the set tested together.
- Phase 1 touches 14 consumer manifests (paths only), the CI sibling lists of six
  repositories, four registry entries, the docsite's list and seven pages.
- robohub-devices keeps equipment and the applications built on it
  (`nodes/gateway-node`); the runtime leaves it.
- A Zephyr adapter, when written, may sit in the collection or beside it; a
  Zephyr module's layout and release cadence decide it then.

## Alternatives considered

- **A kernel from scratch** — low differentiation, permanent cost of ports,
  drivers and fixes. Rejected; kept as a possible Phase 4 backend.
- **A thin umbrella over the existing repositories** — no migration, but four
  repositories kept in step by hand, a compatibility matrix, five sets of
  governance files, for no user who needs the pieces apart. Rejected while the
  pieces change together under one maintainer.
- **A managed runtime (a VM) on the board** — live code updates, but a second Rho
  backend and a large memory cost on small parts. Not now.
- **Edge only, leaving microcontrollers to vendor SDKs** — gives up the node half
  that makes RoboHub distinct. Rejected.
