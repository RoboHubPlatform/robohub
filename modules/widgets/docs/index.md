# Widgets

Configurable dashboard cards for a host application: numbers, charts, tables,
status badges, buttons and switches, each reading a gateway source, an inventory
item, one of the application's own values, a URL or a value typed in. The module
registers its pages on the host's router; it has no port of its own and keeps its
tables in the host's SQL database.

## How an application uses it

Include the module and add it to `deps`. It brings `i18n`, `settings`,
`notifications`, `forms`, `inventory`, `journal`, `appapi` and the
`robohub.gateway` interface, which the application binds to a provider (see
{ref}`robohub-gateway-contract/index`). Its tables and statements come with it
(rho-sql generates them into the application), so an application never repeats
them.

The application:

- defines `host_shell(req, title, body, scripts)`, which wraps the module's
  pages in the application's own layout;
- puts `{{{ widgets_style }}}` (from `widgets_style()`) in its layout, so a card
  looks the same in every application;
- calls `widgets_refresh_all()` from its background worker, and refreshes when
  `widgets_live_changed()` says the gateway's live stream has brought something
  new — so a reading reaches a card as soon as Mesh has stored it, rather than on
  a timer;
- adds the module's settings tab: `widgets_settings_form` and
  `widgets_settings_save`, combined through `host_settings_tabs/form/save` (see
  {ref}`appshell/index`).

## Kinds

| Kind | What the card shows |
|---|---|
| Number (`numeric`) | The latest value, with its unit. |
| Chart (`chart`) | The latest values as a sparkline; a gateway source draws its history. |
| Table (`table`) | The latest values as rows; the widget's point count is the number of rows. |
| Status (`status`) | A badge whose value is the latest text. A prefix `ok:`, `warn:`, `bad:` or `info:` chooses the badge class (the host's `status-pill`); the rest is the text. |
| Button (`button`) | Presses its source when pressed. |
| Switch (`toggle`) | Shows on or off and switches its source to the other state. |

## Sources

| Source kind | What `source` holds | How it is read |
|---|---|---|
| Gateway source (`mesh`) | A gateway source's stable id (`<node id>.<signal>`) | `gateway.source_latest` for a value, `gateway.source_history` for a chart, `gateway.action` for a button or switch |
| Inventory item (`item`) | `handle.capability`, such as `heater.temperature` | Inventory resolves it to the gateway source the item's capability is bound to; a switch goes through `inventory_switch` |
| Application value (`value`) | One of the application's own values | `appapi_value`, kept like a URL's value so a chart has its history |
| URL / hook (`url`) | An `http://` or `https://` URL | Fetched with no credential; a button or switch calls it as a hook |
| Manual (`manual`) | — | Entered on the widget's edit page or through `POST /api/widgets/{id}/value` |

A widget never reads the gateway by its address. The gateway requires a token on
every route except `/healthz`, and the module holds no token: a reading from the
gateway is chosen as a gateway source by its stable id, or as an item's
capability, and is read through the provider the application binds. A URL source
is sent no credential at all, because a URL a person typed into a widget may be
anywhere — use it for something that answers without one.

**Choosing a gateway source.** The edit page lists `gateway.sources()`, separated
by direction: numbers, charts and tables see inputs; buttons and switches see
outputs. Choosing a source fills the method and unit, so a DS18B20 temperature
shows `°C` and a Shelly plug's power shows `W` without the widget knowing either
part. A simulated reading takes the path a real one does — into Mesh, and back
through the same provider.

**A switch for a plug.** Choose the plug's switch output as the gateway source
and kind **Switch**, or choose the plug's inventory item. Pressing it calls
`gateway.action(<source>, "on"|"off")`, and the card shows the state the gateway
reports. For a URL hook, `{state}` in the URL is replaced with `on` or `off`;
without it, `?state=on` or `?state=off` is appended.

Older widgets that stored a Mesh URL or a positional id (`device.3.switch`) are
moved to stable gateway ids by `widgets_migrate_sources()`, which
`widgets_refresh_all()` calls.

## The pages

The manager (`/widgets`) and the edit page are content drawn through
`host_shell`. Card actions happen in place with HTMX: pin and resize return the
one card, move returns the reordered `#widget-cards` grid. Manual value entry
and Press are on the widget's edit page, shown only for a manual widget or a
button or switch.

**Live updates.** The grid follows `/widgets/events` (Server-Sent Events, one
event name per card and locale), and each card also reloads itself every
`widgets.refresh_seconds`. A press emits the new state at once, and a page
render reads the gateway before painting, so a plug switched elsewhere is
correct on the first paint.

## Settings

| Key | Default | What it is |
|---|---|---|
| `widgets.refresh_seconds` | `10` | How often a card reloads itself |
| `widgets.points` | `24` | The point count a new widget starts with |

## Data it keeps

In the application's SQL database (`<workspace>/data/app.db`, or
`RHO_WIDGETS_DB`), from the module's own `db/schema.sql`:

| Table | What it holds |
|---|---|
| `widgets` | Each widget: title, kind, source kind and source, method, unit, points, and its place on the dashboard (position, size, decimals, pinned) |
| `widget_values` | The values stored for a widget (manual, URL and application values), with the time each was recorded |

Additions, saves and removals are logged under the `widgets` subject; a press
is written to the journal.
