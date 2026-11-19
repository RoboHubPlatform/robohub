# Changelog

## [0.1.0] - 2026-11-20

First release (ADR-0017): a data-only plugin Mesh reads — not the keeper — for
every Zigbee coordinator it runs. It pins Zigbee2MQTT 2.14.3, its source tarball
and the container image `ghcr.io/koenkk/zigbee2mqtt:2.14.3` (Z2MP-0001);
declares Node.js `^22.2 || ^24` in `system_deps`, with a fetch of the Node.js
24.22.3 LTS release for x86-64 Linux (and its SHA-256) and the apt and brew
packages, so `rho doctor` reports it and `rho keeper sync` installs it
(Z2MP-0002); and carries `templates/configuration.yaml`, with the broker,
user, base topic, serial port, adapter and channel as placeholders Mesh fills,
the broker password and network key only as `!secret` references, the network
key and PAN ids generated, availability on, and the frontend and Home Assistant
discovery off, at configuration version 5 (Z2MP-0003). `tests/check_template.py`
holds the template to those rules.
