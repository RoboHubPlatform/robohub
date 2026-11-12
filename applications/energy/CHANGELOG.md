## [0.1.0] - 2026-11-09

The first energy application: one location's generation, storage, grid and
loads in one service.

- Multi-source ingestion and normalization for PV strings, microinverters and
  wind turbines, with derived power/current when one figure is absent.
- LiFePO4 bank tracking: SoC, SoH, cell window, temperature and the L51 CAN
  profile.
- Grid import/export, voltage, frequency, synchronization and strict zero export.
- Off-grid, on-grid and hybrid operating modes with load shedding, generator
  thresholds, peak shaving and tariff windows.
- Typed energy and telemetry schemas, generated through the SQL port.
- CSRF-protected admin forms through the forms module, with number and IPv4
  validation.
- Safety interlocks that write power faults into the telemetry SQLite/WAL store.
- The dashboard is the shared widgets module: seeded numeric, status and chart
  cards bound to simulated Mesh sources, per-locale SSE, and a ten-second
  refresh from the application's background worker. Energy no longer renders a
  second dashboard of its own.
- Inventory (`/expenses`), scheduler (`/scheduler`) and widgets (`/widgets`) are
  carried as reusable modules. Their pages render content through the energy
  host shell, so the energy menu, header and footer are the same everywhere.
  Module items are separate menu entries, not an "Apps" group.
- Widget card CSS comes from the widgets module (`widgets_style()`); energy and
  aquarium no longer keep private widget styles. The aquarium home now passes
  that style too, fixing its unstyled cards.
- Widget move, resize and pin controls are in place over HTMX; moving a card
  replaces the grid instead of redirecting to a new page.
- The dashboard shows the current mode as a big badge beside its title with a
  two-second heartbeat; the switch is in Settings, no restart needed. Simulation
  mode disables the Mesh fields; real-time mode disables the scripted-fault
  field. Real-time mode uses the same `mesh-gateway` plugin as the aquarium.
  The Mesh project is a select built from the projects the entered Mesh address
  reports; the telemetry project is derived from that selection instead of being
  a separate input. Each node can name its Mesh source.
- Simulation mode publishes simulated Mesh sources (`energy.generation`,
  `energy.soc`, `energy.faults`, and so on). The widget source picker lists and
  preselects them; switching to real-time clears the simulated selections so a
  real Mesh source can be chosen.
- Energy-specific fault SSE on `/energy/stream` still drives the Faults page,
  in its own `energy-live.events` file, separate from the notifications feed.
- A deterministic, stateful simulator selected by the persisted driver-mode
  setting, with `ROBOHUB_DRIVER_MODE` as the environment default, and scripted
  fault injection for tests and demonstrations.
- A smoke test that runs the whole loop on a workstation with no hardware.

## [0.1.1] - 2026-11-12

Energy declares the robohub-auth plugin, like aquarium; it already used the
keeper's sign-in.

## [0.1.2] - 2026-11-12

Every list read into a fixed array asks for at most what the array holds: the fault lists asked for 128 rows into 32 places. The smoke test signs in with a keeper ticket, checks the telemetry outbox Mesh polls instead of the store energy no longer keeps, and reads the fault state from energy rather than from the dashboard card Mesh feeds.

## [0.1.3] - 2026-11-12

The telemetry outbox is numbered and rewritten under one lock. The simulator
and a request recorded readings at the same time and could give two readings one
number, and an acknowledgement that rewrote the outbox between a read and an
append lost the reading appended. project.yml writes only what differs from the
built-in target, and carries the templates folder whole.
