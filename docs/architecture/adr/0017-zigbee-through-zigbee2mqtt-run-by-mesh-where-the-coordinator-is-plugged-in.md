---
id: ADR-0017
title: Zigbee through Zigbee2MQTT, run by Mesh on the board the coordinator is plugged into
status: accepted
date: 2026-11-20
requirements: [SYS-0069, SYS-0001, SYS-0004, SYS-0028, SYS-0032, SYS-0033, SYS-0051, Z2MP-0001, Z2MP-0002, Z2MP-0003]
supersedes: []
superseded_by: []
---

# Zigbee through Zigbee2MQTT, run by Mesh on the board the coordinator is plugged into

## Context

A person wants Zigbee devices in RoboHub — first a **Sonoff S60ZBTPF**, the
Zigbee version of the iPlug S60 whose Wi-Fi sibling (S60TPF) RoboHub reads
reflashed with Tasmota (robohub-devices ADR-0002) — through a **Sonoff Zigbee 3.0
USB Dongle Plus** as the coordinator. SYS-0001 rules out a vendor hub or cloud;
SYS-0028 and SYS-0051 ask that network equipment report through the local broker
and appear like a board. The person also set a constraint: the coordinator is a
USB radio, so it can only be part of a mesh that has a board able to host it —
this machine (the native gateway) or another host board.

### What exists

- **The broker.** The keeper runs Mosquitto from the data-only plugin
  `robohub-mqtt` as a user service on port 1884, loopback until an admin opens
  it, with a broker user per application that binds `robohub.bus` (the topics
  its `bus:` block names) and per device an admin adds (`readwrite <prefix>/#`)
  (robohub-keeper KEEP-PROV-0005). A keeper *integration* is one service per
  machine; it is not itself a broker user.
- **MQTT devices in Mesh.** A device node of transport `mqtt` is read from the
  topics and field lines of its manifest and switched by its manifest's action
  (robohub-mesh ADR-0009, MESH-0022, MESH-0029…0032). The Tasmota plug needed
  only manifest lines and three contract additions in Mesh.
- **Boards.** A board manifest declares `capabilities` (`host`, `wireless`,
  `links`, `buses`, `deploy`); `usb` in `buses` means a USB device port or a
  serial console, never a USB host. Mesh's native gateway is a synthetic board
  (the machine running the keeper), started as a process with a pid file in the
  mesh's folder. The UNO Q's Linux side deploys over SSH and runs Docker.

### What a coordinator needs

A coordinator is not an MQTT device: it is a radio on a USB serial port that a
host program drives. **Zigbee2MQTT** (2.14.3, November 2026) is that program for
both versions of the dongle — the **ZBDongle-P** (TI CC2652P, `zstack` adapter,
USB 10c4:ea60) and the **ZBDongle-E** (Silicon Labs EFR32MG21, `ember` adapter,
EmberZNet 7.4 or later, USB 1a86:55d4 or 10c4:ea60) [1], [2], [3]. It connects to an
MQTT broker and publishes every device under `<base_topic>/<friendly_name>`, takes
commands on `…/set`, reports availability as `{"state":"online"}` on
`…/availability`, and is administered over `<base_topic>/bridge/request/…` with
responses on `…/bridge/response/…` [4]. It supports the S60ZBTPF (`model`
S60ZBTPF, `vendor` SONOFF) with `state`, `power`, `voltage`, `current`, `energy`,
`energy_today`, `energy_yesterday` and `energy_month` [5].

Facts that shape the decision [4], [6], [7]:

- 2.0 removed the legacy availability payload, the permanent `permit_join`
  (joining is opened for at most 254 s) and the default adapter; a version
  change can break a running installation.
- Without `configuration.yaml`, 2.x starts an onboarding web page on
  `0.0.0.0:8080`; `Z2M_ONBOARD_NO_SERVER` disables it.
- Without explicit values, the network key and PAN ids are built-in defaults
  shared by every installation; `GENERATE` makes them, and Zigbee2MQTT writes the
  generated values back into its configuration (or into `secret.yaml` when the key
  is a `!secret` reference). `mqtt.password` and `advanced.network_key` may be
  `!secret` references.
- A switch takes `"ON"`/`"OFF"`/`"TOGGLE"`; a JSON boolean is refused.
- It needs Node.js 22 or 24 (2.14.3's `engines`), installs from source with
  `pnpm install --frozen-lockfile`, and ships the image `ghcr.io/koenkk/zigbee2mqtt`.

### Where a USB coordinator can be

- **This machine.** Here it is WSL2: the dongle is passed from Windows with
  usbipd-win (`usbipd bind`, `usbipd attach --wsl --auto-attach`); the WSL kernel
  carries `cp210x` and `cdc_acm` [8]. Behind usbipd the `/dev/serial/by-id/`
  name may differ from the vendor's [2].
- **The UNO Q.** Its single USB-C port is role-switching; USB devices are
  plugged in through a powered USB-C hub, and host mode is not enabled when the
  board is powered from 5V/VIN until a header is set [9]. Docker is present [10].
- **Pico, ESP32, STM32, AVR boards.** No USB host and no way to run
  Zigbee2MQTT.

## Decision

Decided by the maintainer on 2026-11-20 (options D1–D5 of the analysis):

1. **Zigbee2MQTT drives every coordinator.** RoboHub writes no Zigbee stack and
   no coordinator protocol; a Zigbee device is an MQTT device Zigbee2MQTT
   publishes.
2. **Mesh owns the coordinator (D1).** A coordinator is a node of a mesh's plan,
   placed under a board of that mesh that declares `host: true` and
   `usb_host: true` (the native gateway counts as both), and Mesh runs
   Zigbee2MQTT for it on that board: on this machine as a process, as it runs the
   native gateway; on another host board as the official container, over the
   board's own deployment. The keeper does not run Zigbee2MQTT.
3. **`usb_host` is a board capability**, declared explicitly (the UNO Q) and
   never inferred from `buses: usb`.
4. **Each coordinator is a broker user of its own**, issued by the keeper to
   Mesh under a topic root Mesh's manifest declares (`bus.issue: [zigbee]`),
   confined to `zigbee/<mesh>/<coordinator>/#` (robohub-keeper ADR-0006). Mesh's
   own credential never leaves Mesh.
5. **Topics:** a coordinator's base topic is `zigbee/<mesh>/<coordinator>`; a
   device's is `<base>/<address>`, its address in the plan, to which Mesh renames
   it in Zigbee2MQTT. Mesh's manifest covers every coordinator with fixed patterns.
6. **Installation (D2).** On a host, Zigbee2MQTT is installed from its release
   source into `~/.rho/toolchains/zigbee2mqtt/<version>` by a Mesh job, with
   Node.js from the plugin's `system_deps` (fetched into `~/.rho/toolchains/`
   by `rho keeper sync`); on a board that runs containers, the image at the same
   version. A data-only plugin, **`robohub-zigbee2mqtt`** in `robohub/plugins/`,
   pins the version and carries the configuration template (Z2MP-0001…0003).
7. **The ZBDongle-P first, the ZBDongle-E beside it (D3)**, both as coordinator
   manifests in robohub-devices; the Dongle Plus MG24 and others are added the
   same way when wanted.
8. **Zigbee2MQTT's own web frontend stays off (D4)**, and so does Home
   Assistant discovery. Pairing, adopting and removing devices are Mesh's pages,
   behind the keeper's sign-in.
9. **The network key moves with a sealed export (D5).** A sealed project file
   carries each coordinator's network key, PAN ids, channel and coordinator
   backup; an unsealed one lists them as omitted, and devices must then be paired
   again.

## Consequences

- **robohub-devices** gains a `coordinator` device kind, manifests for the two
  dongles, and a manifest for the S60ZBTPF with a `zigbee` block for matching
  (robohub-devices ADR-0003).
- **robohub-mesh** gains the coordinator node and its placement rule, Zigbee2MQTT
  as a process or a container, pairing (bounded joining, discovered devices,
  adopt, remove), two device-contract additions (`online_path`, `{ONOFF}`), new
  bus patterns, and the project file's schema 2 (robohub-mesh ADR-0010).
- **robohub-keeper** gains issued broker users (ADR-0006). **robohub-linux**
  declares `usb_host` on the UNO Q.
- A coordinator on the UNO Q reaches the broker on this machine only when an
  admin opens the broker to the network; that traffic is plain MQTT with a
  password, as it is for Tasmota devices. TLS on the broker is a decision of its
  own.
- The person on WSL attaches the dongle with usbipd once per boot unless
  auto-attach is used; while attached, Windows cannot use it.
- A Zigbee2MQTT upgrade is a deliberate change of one pinned version, checked
  against the topics Mesh reads; the host tests hold the documented payloads.
- Zigbee devices are not framed by a device node and do not reach the gateway's
  wire protocol; Mesh reads them as it reads Tasmota and Shelly devices over MQTT.

## Alternatives considered

- **The keeper runs Zigbee2MQTT as an integration**, like Mosquitto — the
  least new code, but one coordinator per machine and only on the keeper's
  machine, against the constraint that a coordinator belongs to a mesh and can
  be on another board; and integrations are not broker users today. Rejected.
- **ser2net on the board and Zigbee2MQTT always on this machine**
  (`serial.port: tcp://…`) — one place to run it, but the coordinator's serial
  link then crosses Wi-Fi, which Zigbee2MQTT warns makes the network unreliable,
  and the board still needs a program and a port opened. Rejected.
- **Zigbee2MQTT in Docker on this machine** — the same everywhere, but on WSL a
  USB device attached to the distribution is not visible to Docker Desktop's VM
  without extra work. Kept for boards that run containers, not used here.
- **ZHA, deCONZ or a vendor hub (eWeLink, the Sonoff iHost)** — ZHA lives inside
  Home Assistant, deCONZ needs its own stick and application, a vendor hub is a
  cloud or another box (SYS-0001). Rejected.
- **A Zigbee stack in RoboHub's own C** — a large subsystem with no benefit over
  a maintained bridge. Rejected.

## Sources

1. Zigbee2MQTT, *Z-Stack adapters* — https://www.zigbee2mqtt.io/guide/adapters/zstack.html
2. Koenkk/zigbee-herdsman, `src/adapter/adapterDiscovery.ts` (USB ids and by-id names of the Sonoff dongles) — https://github.com/Koenkk/zigbee-herdsman/blob/master/src/adapter/adapterDiscovery.ts
3. Zigbee2MQTT, *EmberZNet adapters* (EZSP v13, EmberZNet 7.4.x and later, the ZBDongle-E) — https://www.zigbee2mqtt.io/guide/adapters/emberznet.html
4. Zigbee2MQTT, *MQTT topics and messages* — https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html ; *Device availability* — https://www.zigbee2mqtt.io/guide/configuration/device-availability.html
5. Zigbee2MQTT, *SONOFF S60ZBTPF* — https://www.zigbee2mqtt.io/devices/S60ZBTPF.html ; Koenkk/zigbee-herdsman-converters, `src/devices/sonoff.ts` — https://github.com/Koenkk/zigbee-herdsman-converters/blob/master/src/devices/sonoff.ts
6. Zigbee2MQTT, *2.0.0 breaking changes* — https://github.com/Koenkk/zigbee2mqtt/discussions/24198 ; *Configuration*, *MQTT*, *Adapter settings*, *Zigbee network* — https://www.zigbee2mqtt.io/guide/configuration/
7. Zigbee2MQTT, *Linux installation* and *Docker* — https://www.zigbee2mqtt.io/guide/installation/01_linux.html , https://www.zigbee2mqtt.io/guide/installation/02_docker.html ; release 2.14.3 — https://github.com/Koenkk/zigbee2mqtt/releases/tag/2.14.3 ; on-off converter (booleans refused) — https://github.com/Koenkk/zigbee-herdsman-converters/blob/master/src/converters/toZigbee.ts
8. Microsoft, *Connect USB devices* (WSL) — https://learn.microsoft.com/en-us/windows/wsl/connect-usb ; dorssel/usbipd-win — https://github.com/dorssel/usbipd-win
9. Arduino, *UNO Q* and *UNO Q host mode* — https://docs.arduino.cc/hardware/uno-q/ , https://docs.arduino.cc/tutorials/uno-q/host-mode/
10. Arduino, *ROS 2 on the UNO Q* (Docker present for App Lab) — https://docs.arduino.cc/tutorials/uno-q/ros2-setup/
