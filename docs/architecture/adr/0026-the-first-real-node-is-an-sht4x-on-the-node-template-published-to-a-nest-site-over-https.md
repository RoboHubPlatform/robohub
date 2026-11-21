---
id: ADR-0026
title: The first real node is an SHT4x on the node template, published to a nest site over HTTPS
status: accepted
date: 2026-11-21
requirements: [SYS-0071, SYS-0072]
supersedes: []
superseded_by: []
---

# The first real node is an SHT4x on the node template, published to a nest site over HTTPS

## Context

robohub ADR-0020 named the first real robohub-node node: the settlement's
temperature and humidity sensor, end to end to a widget on morlaca.ro. robohub
ADR-0019 decided how readings leave an installation. robohub-feed pushes static
snapshots outward, so nothing at the settlement or at home is reachable from
outside. Phase 2 (ADR-0021…0025) gave every node the same firmware: the template,
with health and signed updates, verified on a Pico 2 W through Mesh and the
gateway.

Three things are missing for that node:

- **A sensor fit for the job.** Of the drivers, only the DHT11 reads humidity.
  It is coarse (±5 %RH, ±2 °C) and does not last outdoors.
- **A way out to a web site.** robohub-feed 0.1.0 has one publisher kind,
  `directory`, a folder on the machine it runs on. morlaca.ro is to be rebuilt as
  a nest application on a host elsewhere.
- **Something on the site to receive it.** The constraint, from the maintainer:
  a nest site holds no data of the installation's. It keeps only the current
  value and a short history for the widget.

How the settlement itself is connected is not decided. It could have its own
small installation, or report to another. The node, the publisher and the
receiver do not depend on that choice.

## Decision

Decided by the maintainer on 2026-11-21. The settlement node comes before Zephyr
(3a, then 3b). The sensor is an SHT4x on I2C. Delivery is an HTTP publisher with
a nest module. The settlement's topology is decided later, and 3a is built and
tested against the home mesh.

1. **An SHT4x driver and module board** in robohub-drivers, after Sensirion's
   SHT4x datasheet:
   - the driver implements robohub-common's temperature and humidity interfaces
     over the I2C HAL, so it is written for no one board;
   - a measurement is the high-precision command (0xFD), and its six bytes are
     checked by CRC-8 before they become a value;
   - the module board gives the part's address (0x44) and each board's I2C
     pins, and declares the telemetry fields Mesh generates `sensors.c` from.
2. **The node is the template.** Mesh fits the SHT4x module to a Pico 2 W built
   from robohub-node's template, as it fits any module. Nothing in Mesh or the
   template is particular to this node.
3. **robohub-feed gains an `http` publisher.** Each file of a refresh (the
   snapshot and the widget script) is sent with an HTTPS `PUT` to the
   publisher's base URL:
   - the request carries the publisher's bearer token, kept in an owner-only file
     beside the feed file, never in the feed file, the page or the log;
   - plain `http://` is refused, except to the loopback, for tests;
   - a failure is recorded with its reason and tried again on the next refresh
     (FEED-0006).
4. **A nest module receives it** (`nest-feed`, in nest's `modules/`):
   - it accepts a `PUT` of a feed's snapshot that carries the feed's token, and
     keeps the latest snapshot and a short history (the last 48 values);
   - it serves the snapshot and the widget script to the site's own pages,
     same-origin, with a template helper that places the widget;
   - it holds nothing else, so a site that loses its files loses only the
     history.
5. **Checked on the bench, then at the settlement.**
   - The driver is tested on the host against an I2C double. The publisher is
     tested against a local receiver, and the nest module with nest's test
     client.
   - An on-target suite builds and flashes a Pico 2 W with an SHT4x, through
     Mesh and the home gateway, and follows its reading through a feed's `http`
     publisher into a local nest module.
   - Where the settlement's installation runs is a later decision. It changes
     nothing here.

## Consequences

- robohub-drivers: DRV-ENV-0007…0009 (the driver) and DRV-BRD-0005 (the module
  board).
- robohub-feed: FEED-0008 (the `http` publisher). FEED-0006 already lets a kind
  be added.
- nest: a new module, `nest-feed`, documented and tested in nest. nest keeps no
  requirements of its own, so its contract is FEED-0008's receiving side and
  this decision.
- Mesh offers the SHT4x on every board whose platform has I2C (the Pico 2 W and
  the LOLIN32 Lite), with no change of its own.
- 3b, Zephyr with MCUboot for the STM32, follows as its own decision.

## Alternatives considered

- **The DHT11** — no new driver, but coarse, and it does not last outdoors.
  Rejected.
- **A BME280** — adds pressure, but its humidity is half as accurate. Rejected
  for this node; a driver can still come later.
- **The directory publisher and a copy** (rsync or scp on a timer) — no new
  code in the feed, but a second schedule and a second credential to keep.
  Rejected.
- **A static host or bucket** — simple, but morlaca.ro is to be a nest site
  serving its own widget. Rejected.
- **The settlement board reporting home over the internet** — needs the home
  uplink reachable from outside, against ADR-0019. Not chosen. The topology stays
  open.
