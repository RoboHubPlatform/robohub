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
