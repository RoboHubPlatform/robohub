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
