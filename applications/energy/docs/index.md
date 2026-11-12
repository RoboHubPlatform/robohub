# Energy

`energy` is the RoboHub application for one location's power: the generation
lines, the battery bank, the utility connection and the loads, normalized into
one site reading and controlled as one site.

It is a modular monolith in the aquarium sense. It is one HTTP service on one
port, it owns its database and workspace, and the reusable UI modules it carries
(`forms`, `settings`, `notifications`, `i18n`, `htmx`) register on the same
router.

## The five functional areas

### 1. Multi-source ingestion and normalization

Every driver presents the same reading shape, whether it is a PV string, a
microinverter, a wind turbine, a BMS or a grid meter. The application accepts
that shape from the simulator in mock mode or at `POST /api/energy/ingest` in
hardware mode.

A source reports power, voltage, current and temperature. If a device reports
only two of the electrical figures, the third is derived:

- current from power and voltage,
- power from current and voltage.

The store keeps integers in stated units, never floating point:

| Quantity | Column | Unit |
| --- | --- | --- |
| power | `power_w` | watts |
| voltage | `voltage_mv` | millivolts |
| current | `current_ma` | milliamperes |
| temperature | `temperature_mc` | milli-Celsius |
| state of charge | `soc_milli` | thousandths of a percent |
| frequency | `frequency_mhz` | milli-Hertz |
| energy | `energy_today_wh`, `energy_total_wh` | watt-hours |

A LiFePO4 bank also carries the lowest and highest cell, so the delta is visible
without a per-cell table, and the CAN profile the BMS speaks (`L51` by default).

### 2. Topology and operating mode control

The site has one of three modes:

- **Off-grid (island)** — the site forms its own voltage reference. Discretionary
  loads are shed at the low-SoC threshold, and the emergency generator starts at
  its start threshold and stops at its stop threshold.
- **On-grid** — the utility is the reference. Synchronization is a safety rule,
  not a display, and zero export is enforced as a policy.
- **Hybrid** — generation and storage take the surplus, the battery covers a
  peak-tariff deficit, and off-peak grid energy charges the bank. Peak shaving
  and tariff optimization are explicit policy switches.

### 3. Safety, thresholds and fault integration

The safety layer evaluates every tick:

- generation line back-sheet temperature, overvoltage and overcurrent,
- battery temperature, low SoC, cell imbalance, charge voltage and discharge
  cutoff,
- grid voltage, frequency, zero-export violation and synchronization.

A fault is recorded on the **edge** into the bad condition, not on every tick of
it, so a dashboard shows one badge for one condition. The transition is kept in
`energy_fault_state`, which the faults page lists; the fault also leaves through
the outbox as a reading with a fault status, so Mesh records it as the project's
fault and every telemetry consumer of the project sees it.

### Telemetry: produced here, owned by Mesh

Energy keeps no telemetry store. Every reading it produces — simulated, typed in,
or posted to `/api/energy/ingest` — is appended to an outbox in its workspace,
readable by its own user only, and served the way a gateway serves one:

```
GET  /energy/gateway/api/v1/telemetry/outbox?after=SEQ&limit=N
POST /energy/gateway/api/v1/telemetry/ack     {"seq": SEQ}
```

A Mesh project whose `gateway_url` is `http://<host>:8482/energy/gateway` and whose
`gateway_audience` is `energy` ingests it: Mesh polls with a short-lived service
token for `energy` carrying the `energy:gateway` scope, stores each reading once,
and streams it to whoever reads the project. What energy shows comes back the same
way, through Mesh's API.

### 4. Configuration and schema management

Typed schemas live in `db/schema.sql`, and the SQL port generates the models and
the query functions from the same files the pages use. Admin forms are rendered
by the `forms` module, carry its CSRF token, and use its number and IPv4 rules
before a value reaches the policy table:

- charging and discharging currents,
- charge voltage and discharge cutoff,
- export limit and zero export,
- solar and battery temperature limits,
- grid voltage and frequency windows,
- the operating mode and the tariff window.

Every change is written to `energy_events`, which is the audit trail the Events
page reads.

### 5. Real-time UI and SSE rendering

The dashboard is the **widgets module's** dashboard. Energy seeds widget
definitions and supplies their values through the gateway provider or the small
JSON/text endpoints; it does not render a second dashboard of its own. The
module owns the card markup, values, layout, per-locale SSE events, refresh and
the widget CSS (`widgets_style()`), which the energy layout includes:

- `GET /widgets` — the widget manager,
- `GET /widgets/events` — the card SSE feed every dashboard uses,
- `GET /api/energy/widgets/{field}` — the value a seeded card reads,
- `POST /api/energy/widgets/refresh` — pull every URL source once.

The seeded energy cards are generation, load, battery SoC and temperature, grid,
site mode, active power faults, and a generation chart. Each is bound to a
simulated Mesh source such as `energy.generation`; the source picker preselects
it in simulation mode. The status cards render `ok:`, `warn:`, `bad:` and
`info:` values as badges. Energy's background calls `widgets_refresh_all()` on a
ten-second cadence; the widgets module refreshes the sources and emits the same
`widget-<id>-<locale>` events a manual page load uses.

Widget cards refresh every ten seconds and through the widgets SSE feed. Move,
resize and pin controls are HTMX actions: moving a card returns the reordered
grid fragment and the dashboard does not reload. `GET /energy/stream` remains the
energy-specific fault feed for the Faults page and carries only `faults` and
`faults-rows`. It uses its own
`energy-live.events` file, so it can never be mistaken for the notifications
module's `live.events` feed. That separation is what keeps a dashboard tick from
appearing as an "Updated" toast.

## Reusable modules

Energy is a modular monolith, not a collection of bespoke screens. It carries the
same reusable modules as the aquarium:

| Module | Route | What energy uses it for |
| --- | --- | --- |
| `inventory` | `/expenses` | spares, consumables and stock for the site |
| `scheduler` | `/scheduler` | maintenance tasks and chore rotations |
| `widgets` | `/widgets` | the single dashboard, card and SSE implementation |

The widgets module is the one reference for widgets across applications. A new
application seeds definitions and supplies values; it does not copy the widget
markup, invent a second SSE protocol, or render its own dashboard. The module's
card CSS lives in `templates/partials/widgets-style.html` and is exposed as
`widgets_style()`; energy and aquarium include it in their layouts instead of
keeping private widget styles.

The module pages are content, not documents. `inventory`, `scheduler` and
`widgets` call the host's `host_shell(req, title, body, scripts)`, which wraps
the content in the application's own layout and menus. The module keeps only its
own content CSS, so opening `/expenses` from energy shows energy's header,
footer and menu, and opening it from aquarium shows aquarium's.

## Driver seam, simulation and real-time Mesh

The application never talks to a register, a Modbus address or a CAN frame. The
driver seam is a persisted setting with an environment default:

```sh
# The environment default for a new workspace
ROBOHUB_DRIVER_MODE=mock
```

The dashboard shows the current mode as a badge beside its title. The badge
carries a two-second heartbeat, so a simulation that is running is visibly alive.
The switch is in **Settings → Driver mode**; the setting is read on every
background tick, so switching between simulation and real-time does not need a
restart. Simulation mode disables the Mesh URL, project and token fields;
real-time mode disables the scripted-fault field.

In **simulation** mode the stateful mock keeps the plant in the application's own
tables, advances a solar bell curve and a wind band, charges and discharges the
bank within the BMS current limits, and respects the operating mode.

In **simulation** mode the simulator's readings take the path real ones do: out
through the outbox into Mesh, and back through the gateway interface. There
is no second, simulated data path to keep in step with the real one.

In **real-time** mode the application uses the same gateway an aquarium uses: the
gateway interface, bound to the Mesh provider. Settings keeps the Mesh URL and
project and writes them into the binding's settings (`bind.conf` in the
application's workspace; the token is the application's short-lived service
token, never a setting), and the gateway answers with the real project's
sources. The **Mesh project is a select populated from
`GET /mesh/api/projects` at the entered address**, so only projects the Mesh
server reports can be chosen; save the URL once to load them. The telemetry
project is not a separate input: it is the selected Mesh project, and the
readings go to the Mesh telemetry store. The simulated source selections are
cleared on the switch, so the operator picks a real Mesh source in the widget
manager. Each generation line, battery bank and grid link also carries a **Mesh
source**; the provider's latest value is the node's primary reading — power for a
line, state of charge for a bank, signed watts for a grid meter.

The Settings page shows the selected driver mode, the configured Mesh project,
the gateway URL, the provider's telemetry status and the Mesh sources as a
full-width readable table (source, kind, signal, direction, unit and ID), so switching from
simulation to real-time shows what it will read before the first tick.

On a C/ESP32 build the same seam is a compile-time choice (`#ifdef SIMULATION`)
so the mock is stripped from a node image. A real driver in `robohub-devices`
presents the same `PowerReading`; this Go service only sees the shape.

## Mesh client handshake

In real-time mode energy registers itself with Mesh as a client of the selected
project. Mesh learns the application name, instance, callback URL and topic
subscriptions; the registration returns a per-client secret that authenticates
Mesh's callbacks to `/api/energy/mesh/events`.

Energy heartbeats every thirty seconds, so Mesh reports it online while the
process is running. It publishes `energy.fault` when a safety rule trips or
clears and `energy.mode` when the operating mode changes. The application does
not need to know which other applications are listening; Mesh matches the topic
and routes the message to subscribers.

The Mesh settings page and the energy dashboard reach Mesh through the same
gateway as the aquarium. The project select is populated from
`/mesh/api/projects`. Every request carries the application's short-lived
service token for Mesh, scoped to the project, which the runtime gets with the
credential the keeper started the application with; nothing is copied into a
setting.

## Logging

Settings has a **Logging** form: level (`trace` to `fatal`), `text` or `json`,
the app log file, its maximum size, how many rotated files to keep, and whether
records also go to standard error. The default file is
`$XDG_STATE_HOME/robohub/energy/app.log` (`~/.local/state/robohub/energy/app.log`).
The app configures the logger at startup and after the form is saved; included
modules write to the same file.

## Scripted faults

The simulator can present a named condition on every tick until cleared:

- `pv_overvoltage`, `pv_overtemp`,
- `battery_overtemp`, `battery_low`, `cell_imbalance`,
- `grid_overvoltage`, `grid_undervoltage`, `grid_frequency`,
- `zero_export`, `grid_offline`.

```sh
curl -X POST -d fault=pv_overtemp http://127.0.0.1:8482/api/energy/sim/fault
curl -X POST -d fault=none       http://127.0.0.1:8482/api/energy/sim/fault
```

`POST /api/energy/ingest` accepts the same reading fields as JSON or a form and
normalizes them. `GET /api/energy/state` is the JSON summary the dashboard and a
smoke test read; `GET /api/energy/events` returns the latest audit events.

## Running

Start it from the keeper's Applications page: the keeper installs it as a user
service with the deploy script it carries, building it from its folder or, once
it is published with `rho module publish`, running the program its package
carries. Energy runs on port `8482`, with the same
unit shape, workspace and restart policy as mesh and aquarium.

```sh
# The keeper controls the service
systemctl --user status energy.service
journalctl --user -u energy.service
```

Its app log is the one from the Logging settings, by default
`~/.local/state/robohub/energy/app.log`, and the Applications page has a Log
link for it.

## Testing

The smoke test builds the application, starts it against a temporary workspace,
walks every page, exercises the forms with their CSRF tokens, injects a scripted
fault, checks the SSE stream, clears the fault, switches to off-grid mode, and
reads the SQLite/WAL store.

```sh
rho test applications/energy --tag smoke
```

## Safety note

This application is a controller and an observability surface. A real site's
protection, anti-islanding, grid-forming and battery limits are the responsibility
of the certified inverter, BMS and protection equipment. The thresholds here are
the application's policy, not a substitute for that equipment.
