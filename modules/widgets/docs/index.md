# Widgets

Configurable dashboard cards for a host application. The module registers
`/widgets` and `/api/widgets` on the host's router; it has no port of its own and
keeps its tables in the host's main SQL database.

## Kinds

- **Number** — the latest value, with its unit.
- **Chart** — the latest values as an inline sparkline.
- **Table** — the latest values as rows; the widget's point count is also the
  number of rows to show.
- **Button** — calls a configured hook or API when pressed.
- **Status** — a badge whose value is the latest text. A `prefix:` is read as
  the state: `ok:`, `warn:`, `bad:` and `info:` choose the badge class; anything
  after the colon is the text. The class is the host's `status-pill` class, so a
  status card uses the same badge vocabulary as the rest of the application.
- **Switch** — toggles between on and off, calls the hook with the new state, and
  shows the current state in the card. The hook may use `{state}`; without it,
  `?state=on` or `?state=off` is appended.

## Sources

`manual` values are entered in the manager or through
`POST /api/widgets/{id}/value`. `url` values are fetched from a URL that returns
a plain number; the manager stores each fetch as a new value. A button or switch
uses the URL as a hook.

With a Mesh URL and project in Aquarium settings, **Mesh source** lists the
project's signals. The list is separated by kind: number, chart and table
widgets see only inputs; buttons and switches see only outputs. Choosing a
source fills the URL, method and unit, so a DS18B20 temperature shows `°C` and a
Shelly plug's power shows `W` without the widget knowing either part.

## API

| Method | Path | Meaning |
|--------|------|---------|
| `GET` | `/api/widgets` | widgets with their latest value |
| `POST` | `/api/widgets/{id}/value` | add a value |
| `POST` | `/api/widgets/{id}/press` | press a button or toggle a switch |

## Host shell and card styles

The module's manager and edit pages are content, not full documents. They call
the host's `host_shell(req, title, body, scripts)`, which wraps the content in
the application's own layout, header, footer and menus. Aquarium and energy
both provide that function; a new host provides the same four-argument function
and gets the module's pages inside its own shell.

Card actions are in place. Pin and resize return the single card; move returns
the reordered `#widget-cards` grid, so a dashboard updates without a redirect.
The controls use HTMX rather than ordinary form posts. Manual value entry and
Press are not in the widget table; they live on the widget's Edit page and are
shown only for manual or button/toggle cards, so a table of mesh- or URL-backed
widgets has just Edit and Delete.

The card CSS is part of the module, not the host. `widgets_style()` returns
`templates/partials/widgets-style.html`; a host includes `{{{ widgets_style }}}`
in its layout. The rules use the host's colour variables where they exist and
fall back to the module's own palette, so a card looks the same in aquarium and
energy without either application copying the grid, card, value, switch or
control rules.

## One implementation for every application

The module's `db/schema.sql` and `db/queries.sql` are the canonical widget table
and statement set. A host includes those tables in its SQL port and lets the
module apply its own schema at runtime; it does not keep a second widget table
or a second card renderer. The card templates, per-locale SSE event names and
refresh behaviour are all here.

`widgets_refresh_all()` is the host seam for background refresh. A host calls it
from its worker; the module fetches every URL source, stores the values that
changed, and emits the same per-locale card events the dashboard already
consumes. The host supplies values; it never renders a widget.

## Sources

The sources come from the gateway interface the host binds (`robohub.gateway`):
the picker lists `gateway.sources()`, a number reads `gateway.source_latest`, a
chart `gateway.source_history`, and the live cards follow `gateway.follow`. The
widgets module knows the fields of a source, not which provider produced them.
A simulated reading takes the path a real one does: into Mesh, and back through
the same provider.

## Storage and settings

Widget definitions and values live in the host's main SQL database. No widget
setting is stored beside the module: the host application owns the route, the
database and the workspace.


## A switch for a Shelly plug

A toggle widget can drive a plug through the gateway device API. Set the Mesh URL and project in Aquarium settings; the widget editor then lists
the project's signals. Choose the plug's **Switch** in **Mesh source**, kind **Switch**, and the URL is filled
with the Mesh action endpoint, which drives the gateway switch endpoint:

```
http://gateway:8080/api/v1/devices/1/switch
```

The widget appends `?state=on` or `?state=off` (or substitutes `{state}` if the
URL contains it). Register the plug on the gateway first; the gateway's
`/api/v1/devices` API polls it and keeps its state.


## Live updates

The dashboard opens `/widgets/events` as Server-Sent Events and also reads
`/api/widgets` every two seconds as a fallback. A page render reads the gateway
before painting, so a plug switched in another tab or application is correct on
the first paint; a press emits `widget:<id>:<state>` immediately.

## Mesh telemetry history

A chart or table bound to a Mesh source calls `gateway_source_history` and draws
the returned series; it does not rely on the widget's local value snapshots. A
day is requested at 15-minute resolution, so a chart stays readable and a table
shows the newest points first. Existing widgets that stored a Mesh value URL are
recognized automatically. New widgets can choose **Mesh telemetry** in the
source-kind selector, which stores the source ID instead of its URL.

A numeric widget keeps reading the source's latest value, which Mesh serves from
its telemetry store before falling back to the device.

Widget additions, saves and removals are written to the host application log under the `widgets` subject.
