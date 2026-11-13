# RoboHub application shell

`appshell` is what every RoboHub application on the gateway draws the same way,
so each draws it once.

## What it serves

| Route | What it is |
|---|---|
| `GET /settings`, `POST /settings` | Where readings come from (Mesh or the simulator, Mesh's project and transport), the inventory's, the scheduler's and the dashboard's settings, logging, and an about tab |
| `GET /docs` | The application's own `docs/index.md` |

## What an application gives it

```rho
fn host_app() string { return "aquarium" }        // its name: assets, logging
fn host_app_title() string { return "Aquarium" }  // how the top bar shows it
fn host_shell(req: Request, title: string, body: string, scripts: string) Response
```

## The pieces an application draws its shell with

- `appshell_rail_link(req, href, icon, label, extra, phone)` — a place on the rail; `phone` keeps it in a phone's bottom bar.
- `appshell_rail_tail(req)` — the system group: settings and docs.
- `appshell_count(n, css)` — a count beside a place.
- `appshell_middle(req, quick_mode, quick_label)` — the top bar's middle: where readings come from, the mode, and a button that starts the application's quick mode or ends the one in force.
- `appshell_topbar(req, middle)` — the top bar.
- `appshell_toast(message)` — a message shown once the page has loaded.

The chips are styled by the class `app-chip` (`ok`, `mode`); an application's
layout gives them their look.
