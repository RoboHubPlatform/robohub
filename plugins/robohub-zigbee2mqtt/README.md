# robohub-zigbee2mqtt

Zigbee for RoboHub: **Zigbee2MQTT**, the program that drives a Zigbee
coordinator, pinned to one version, with what it needs from the machine and the
configuration template it is started with (ADR-0017). It has no code of its own.

A Zigbee coordinator — a USB radio such as the Sonoff ZBDongle-E — is a node of a
mesh's plan, placed under a board that declares `host` and `usb_host`. **RoboHub
Mesh runs Zigbee2MQTT for it, on that board, once per coordinator; the keeper
does not.** The keeper is not given this plugin to run: it is not listed in
`plugins/registry.yml`, and it declares no `integration.service`. Mesh finds it
through its registry entry, `registry/modules/robohub-zigbee2mqtt.yml`, as it
finds robohub-devices, and reads the lines below.

## What it declares

| | | Requirement |
|---|---|---|
| `zigbee2mqtt.version` | `2.14.3`, the one version every coordinator runs | Z2MP-0001 |
| `zigbee2mqtt.source` | the release's source tarball, installed on a host into `~/.rho/toolchains/zigbee2mqtt/2.14.3` | Z2MP-0001 |
| `zigbee2mqtt.image` | `ghcr.io/koenkk/zigbee2mqtt:2.14.3`, for a board that runs containers (the UNO Q) | Z2MP-0001 |
| `zigbee2mqtt.node_major` | `22`, `24` — the Node.js majors 2.14.3 supports (`engines`: `^22.2.0 \|\| ^24`) | Z2MP-0002 |
| `system_deps` | `node` `^22.2 \|\| ^24`, fetched from nodejs.org (24.22.3 LTS, x86-64 Linux, with its SHA-256) or installed with apt/brew | Z2MP-0002 |
| `zigbee2mqtt.config` | `templates/configuration.yaml`, the template Mesh fills for each coordinator | Z2MP-0003 |

An upgrade of Zigbee2MQTT is a change of these lines and a release note, checked
against the topics Mesh reads: 2.0 changed topics and configuration without a
compatibility mode, so the version never moves by itself.

## What the machine needs

`rho doctor` reports Node.js against the plugin's `system_deps`, and `rho keeper
sync` fetches the official Node.js 24 LTS release into `~/.rho/toolchains/` when
the one on the machine is missing or older than 22.2 — distribution packages
often are (Debian 12 ships 18). On a host Mesh then installs Zigbee2MQTT from the
source tarball with that Node.js on `PATH`:

```sh
# what Mesh's install job does, in ~/.rho/toolchains/zigbee2mqtt/2.14.3
corepack pnpm install --frozen-lockfile
# and how it starts one coordinator's Zigbee2MQTT
ZIGBEE2MQTT_DATA=<the coordinator's data dir> Z2M_ONBOARD_NO_SERVER=1 node index.js
```

`Z2M_ONBOARD_NO_SERVER` keeps Zigbee2MQTT from opening its onboarding (and
failure) web page on `0.0.0.0:8080`.

## The configuration template

`templates/configuration.yaml` is written into each coordinator's data
directory with these placeholders filled by Mesh:

| Placeholder | What Mesh puts there |
|---|---|
| `{coordinator}`, `{mesh}` | the coordinator node and the mesh, in the header comment |
| `{server}` | the keeper's broker, `mqtt://<host>:1884` |
| `{user}` | the broker user the keeper issued to Mesh for this coordinator (also the MQTT client id) |
| `{base_topic}` | `zigbee/<mesh>/<coordinator>` |
| `{serial_port}` | the dongle's `/dev/serial/by-id/` path |
| `{adapter}` | the coordinator manifest's `zigbee.adapter` (`ember`, `zstack`, ...) |
| `{channel}` | the Zigbee channel, 11 to 26 |

What the template fixes, whatever Mesh fills (Z2MP-0003):

- **No secret in it.** `mqtt.password` and `advanced.network_key` are only
  `!secret password` and `!secret network_key`, references to `secret.yaml`,
  which Mesh writes beside it, owner-only, with the broker password and
  `network_key: GENERATE`. The template is published; a secret in it would be
  published with it.
- **Generated network identity.** The network key, PAN id and extended PAN id are
  `GENERATE`: Zigbee2MQTT makes them on its first start and writes them back
  (the key into `secret.yaml`). Its built-in defaults are the same in every
  installation.
- **Device availability on**, so a device that stops answering is shown
  unreachable (`<prefix>/availability`).
- **The web frontend and Home Assistant discovery off.** Pairing, adopting and
  removing devices are Mesh's pages, behind the keeper's sign-in; nothing Mesh
  does not use listens.
- `version: 5`, the configuration-file version Zigbee2MQTT 2.14.3 writes
  (`CURRENT_VERSION` in its `lib/util/settings.ts`); an older one is migrated and
  rewritten on start. Only `mqtt.server` is required by its schema; the rest are
  what RoboHub needs.

`tests/check_template.py` holds the template to these rules (Z2MP-0003).
