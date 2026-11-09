# Changelog

## [0.2.3] - 2026-11-09

Host-shell pages, module-owned card CSS through `widgets_style()`, a `status`
card for ok/warn/bad/info badges, simulated Mesh sources with preselection and
reset, Mesh-source selection in the add/edit forms, and in-place move, resize
and pin actions over HTMX. `widgets_refresh_all` lets a host background worker
refresh sources and emit per-locale card events. The module's `db/schema.sql`
and `db/queries.sql` are the canonical card layout and statement set, and both
host homes now include the card CSS.

## [0.2.2] - 2026-11-08

English/Romanian cards and admin UI, forms-engine add flow, translated/notified
presses, and per-locale SSE events for translated cards.

## [0.2.1] - 2026-11-06

Fixed widget_json_number_field to parse decimal points (was truncating to
integers). Chart now uses 2h window instead of 24h for responsiveness.

## [0.2.0] - 2026-11-05

A chart or table bound to a Mesh source now reads the source's telemetry
history rather than the widget's local value snapshots. Existing widgets that
stored a Mesh value URL are recognized without migration; new widgets can choose
**Mesh telemetry** and store the source ID. A numeric widget still reads the
latest value, which Mesh serves from its store.

## [0.1.8] - 2026-11-04

Widget fetches and press hooks send the gateway service token, so a widget pointing at a protected Mesh source still reads values and drives outputs.

## [0.1.7] - 2026-11-03

A widget can bind to a Mesh project's signals: number, chart and table widgets
see inputs, while buttons and switches see outputs. Choosing a source fills its
URL, method and unit, so a part's unit is shown without retyping it. There is a
new **Table** kind whose rows are the widget's point count.

## [0.1.6] - 2026-11-03

A dashboard render syncs the toggle states from the gateway before painting, and
a press emits its SSE event. The dashboard also falls back to `/api/widgets`
every two seconds if the event stream is unavailable.

## [0.1.5] - 2026-11-03

The switch text is no longer styled as a second switch track, and an SSE
connection starts from a snapshot of the current states instead of replaying
the event history.

## [0.1.4] - 2026-11-03

Widgets update live: a switch is refreshed from the gateway and the change is
delivered as a Server-Sent Event (`/widgets/events`), so a plug switched outside
the page changes its card without a reload. Pressing a switch stays on the
dashboard and updates the control in place.

## [0.1.3] - 2026-11-03

A switch card shows only the switch, larger and without the card border; its
title opens the widget settings. Pressing it from a dashboard stays there,
while the manager's Press button stays in the manager. A dashboard can always
offer **+ Add widget**.

## [0.1.2] - 2026-11-03

The widget device list resolves the gateway through a selected Mesh project
(`/mesh/api/projects/{project}/gateway`) instead of a gateway address stored by
Mesh.

## [0.1.1] - 2026-11-03

The widget editor can list devices from a connected Mesh/gateway and fill the
source with a chosen device's switch endpoint.

## [0.1.0] - 2026-11-02

Dashboard widgets with a configurable source: a number, a chart of recent
values, a button that calls a hook, and a switch that calls its hook with the new
state and shows that state. Values and definitions live in the host's main SQL
database; the manager and the API register on the host's router.
