# Widgets

Configurable dashboard cards for a host application. The module registers
`/widgets` and `/api/widgets` on the host's router; it has no port of its own and
keeps its tables in the host's main SQL database.

## Kinds

- **Number** — the latest value, with its unit.
- **Chart** — the latest values as an inline sparkline.
- **Button** — calls a configured hook or API when pressed.
- **Switch** — toggles between on and off, calls the hook with the new state, and
  shows the current state in the card. The hook may use `{state}`; without it,
  `?state=on` or `?state=off` is appended.

## Sources

`manual` values are entered in the manager or through
`POST /api/widgets/{id}/value`. `url` values are fetched from a URL that returns
a plain number; the manager stores each fetch as a new value. A button or switch
uses the URL as a hook.

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
the devices from the project's gateway. Choose one in **Mesh device**, kind **Switch**, and the URL is filled
with the gateway switch endpoint:

```
http://gateway:8080/api/v1/devices/1/switch
```

The widget appends `?state=on` or `?state=off` (or substitutes `{state}` if the
URL contains it). Register the plug on the gateway first; the gateway's
`/api/v1/devices` API polls it and keeps its state.


## Live updates

The dashboard opens `/widgets/events` as Server-Sent Events. A refresh request
(`POST /widgets/refresh`) reads the gateway's device states and emits a
`widget:<id>:<state>` event when a toggle changed, so a plug switched outside
the page updates without a reload.
