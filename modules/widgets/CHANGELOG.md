# Changelog

## [0.1.0] - 2026-11-02

Dashboard widgets with a configurable source: a number, a chart of recent
values, a button that calls a hook, and a switch that calls its hook with the new
state and shows that state. Values and definitions live in the host's main SQL
database; the manager and the API register on the host's router.

## [0.1.1] - 2026-11-03

The widget editor can list devices from a connected Mesh/gateway and fill the
source with a chosen device's switch endpoint.

## [0.1.2] - 2026-11-03

The widget device list resolves the gateway through a selected Mesh project
(`/mesh/api/projects/{project}/gateway`) instead of a gateway address stored by
Mesh.

## [0.1.3] - 2026-11-03

A switch card shows only the switch, larger and without the card border; its
title opens the widget settings. Pressing it from a dashboard stays there,
while the manager's Press button stays in the manager. A dashboard can always
offer **+ Add widget**.

## [0.1.4] - 2026-11-03

Widgets update live: a switch is refreshed from the gateway and the change is
delivered as a Server-Sent Event (`/widgets/events`), so a plug switched outside
the page changes its card without a reload. Pressing a switch stays on the
dashboard and updates the control in place.

## [0.1.5] - 2026-11-03

The switch text is no longer styled as a second switch track, and an SSE
connection starts from a snapshot of the current states instead of replaying
the event history.

## [0.1.6] - 2026-11-03

A dashboard render syncs the toggle states from the gateway before painting, and
a press emits its SSE event. The dashboard also falls back to `/api/widgets`
every two seconds if the event stream is unavailable.

## [0.1.7] - 2026-11-03

A widget can bind to a Mesh project's signals: number, chart and table widgets
see inputs, while buttons and switches see outputs. Choosing a source fills its
URL, method and unit, so a part's unit is shown without retyping it. There is a
new **Table** kind whose rows are the widget's point count.

## [0.1.8] - 2026-11-04

Widget fetches and press hooks send the gateway service token, so a widget pointing at a protected Mesh source still reads values and drives outputs.

## [0.2.0] - 2026-11-05

A chart or table bound to a Mesh source now reads the source's telemetry
history rather than the widget's local value snapshots. Existing widgets that
stored a Mesh value URL are recognized without migration; new widgets can choose
**Mesh telemetry** and store the source ID. A numeric widget still reads the
latest value, which Mesh serves from its store.

## [0.2.1] - 2026-11-06

Fixed widget_json_number_field to parse decimal points (was truncating to
integers). Chart now uses 2h window instead of 24h for responsiveness.

## [0.2.2] - 2026-11-08

English/Romanian cards and admin UI, forms-engine add flow, translated/notified
presses, and per-locale SSE events for translated cards.

## [0.2.3] - 2026-11-09

Host-shell pages, module-owned card CSS through `widgets_style()`, a `status`
card for ok/warn/bad/info badges, simulated Mesh sources with preselection and
reset, Mesh-source selection in the add/edit forms, and in-place move, resize
and pin actions over HTMX. `widgets_refresh_all` lets a host background worker
refresh sources and emit per-locale card events. The module's `db/schema.sql`
and `db/queries.sql` are the canonical card layout and statement set, and both
host homes now include the card CSS.

## [0.2.4] - 2026-11-12

The module declares the runtime functions it calls rather than relying on the including application. Its smoke test signs in with a keeper ticket and sends the form token the module checks; a widget's latest value is read back again with the toolchain's fix for arrays a database read fills.

## [0.2.5] - 2026-11-12

Sources, readings, history and the live stream come from the gateway interface the host binds (`gateway.sources()`, `gateway.source_latest(...)` ...); the module declares `robohub-gateway` and imports it rather than calling the functions of a contract its host included.

## [0.2.6] - 2026-11-13

The module declares its tables and statements in its own `sql:` block, and
rho-sql 0.2 generates them into each application that depends on it, so an
application no longer repeats them. The smoke test runs in the aquarium's own
repository.

## [0.3.0] - 2026-11-13

A widget reads a gateway source by its stable id, an inventory item's capability
by handle (`heater.temperature`, through the source the item is bound to), or one
of the application's own values (appapi); plain URLs remain for what is not a
gateway. A toggle on a gateway source or an item switches through the gateway or
inventory, not with a request carrying a token. Sources older widgets stored — a
Mesh URL, a positional id — move to stable ids by the legacy ids the gateway
lists. Presses are written to the journal rather than to a table of the host's;
the JSON API's press reads the toggle's own state, not the state of the widget at
the same position.

## [0.3.1] - 2026-11-13

A widget's URL is passed to curl as one argument, with no shell and only over http or https, so a source can no longer carry options of its own (`-o`, `--data @file`). The gateway's token is sent only to the gateway's own URL, never to an address a person typed into a widget. The method is GET, POST or PUT.

## [0.3.2] - 2026-11-13

A URL widget's answer is read as a value (`rho_exec_capture`) rather than from a per-widget file a refresh and a page could both be writing. The clock is read from the process (`rho_now_s`, rho 0.6.0) instead of from `date` written to a file and read back, which a request and the background loop could truncate under each other: entries dated 1970 and modes that expired at once.

## [0.3.3] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0. A reading with a decimal comma reads as its value.

## [0.3.4] - 2026-11-14

Widgets no longer call the inventory's `ignore_result`, which they reached only because an application included both: they have `widgets_ignore`. `VALUE_CAPACITY` is `WIDGETS_VALUE_CAPACITY`.

## [0.3.5] - 2026-11-14

Its data is kept where `app_workspace()` says (rho 0.8.0) — the application's workspace, else `~/.rho/apps/<app>` — so two applications started by hand no longer share this module's records. Copies of helpers the toolchain now provides (`i64_to_str`, `str_lower`, `str_field`, `json_str_field`, `escape_html`) are gone. It declares the i18n module it uses. Needs rho 0.8.0.

## [0.3.6] - 2026-11-14

Its settings form is its own (`widgets_settings_form`, `widgets_settings_save`). A URL widget sends no credential: the gateway's token was sent to any address under the gateway's, where a gateway source is read through the gateway interface.

## [0.4.0] - 2026-11-14

The live stream of cards (`events.jsonl`) is appended to instead of read and written whole on every change, and starts over every 500 writes. An installation that had run for days kept a file of hundreds of megabytes and rewrote it on each widget update, which held a CPU busy and the memory high. A page following the stream picks up from the top when it starts over, and each event carries a whole card, so nothing is lost. The smoke tests wait longer for a slow host and no longer assume the state a plug starts in. It also lists what other code may use (`provides.exports`, imported as `robohub.widgets`). An application that includes it still reaches everything, and a build (rho 0.8.3) names each call to a function outside the list. The list is what the applications and modules of the ecosystem call; anything else is the module's own and may change without notice. Its JSON splitter is one of its own: Energy, which borrowed it, now has its own copy.
