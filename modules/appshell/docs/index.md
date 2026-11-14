# RoboHub application shell

`appshell` is the part every RoboHub application draws the same way: the
settings page, the docs page, and the pieces of the shell around them (the
rail's links, the top bar with where readings come from and the mode in force,
a toast). Aquarium and energy include it, so each draws these once.

## How an application uses it

Include the module and add it to `deps` (`robohub: appshell: ">=0.2.0"`). It
brings `ui`, `forms`, `settings`, `i18n`, `logging`, `rules`, `journal` and the
`robohub.gateway` interface with it, so the application binds `robohub.gateway`
to a provider in its `bind:` block (see {ref}`robohub-gateway-contract/index`).

The application keeps its own rail and layout and answers the module's
questions through host hooks:

- `host_app()` — its name (`aquarium`): which assets the docs page reads and
  which logger the logging tab configures.
- `host_app_title()` — how the top bar shows it (`Aquarium`).
- `host_shell(req, title, body, scripts)` — draws a page inside the
  application's layout. The settings and docs pages, and every module's pages,
  are drawn through it.
- `host_settings_tabs()`, `host_settings_form(req, tab, action)`,
  `host_settings_save(req, tab, body)` — the settings tabs the application adds
  for the modules it includes (see below).

## The settings page

`GET /settings` shows one tab at a time (`?tab=<key>`); `POST /settings` saves
the tab that was posted, after checking the form's CSRF field. The tabs are:

| Tab | Whose | What it holds |
|---|---|---|
| `gateway` | appshell | Where readings come from (`robohub-provider-mesh` or the simulator), Mesh's project (listed from Mesh) and the transport (`auto`, `bus`, `http`). They are the gateway provider's own settings, kept through `robohub.gateway`. Mesh's address and the token it is read with come from the keeper, never from this page. |
| one per module | the module | Whatever the application lists in `host_settings_tabs()` |
| `logging` | `logging` | The application's log level and outputs |
| `about` | appshell | The application's name, the gateway provider and transport, and the application's API (`/api/v1/values`, `/api/v1/events`) |

appshell knows no module's settings. Each module that has settings provides its
own form and save function (`inventory_settings_form`/`inventory_settings_save`,
`scheduler_settings_form`/`scheduler_settings_save`,
`widgets_settings_form`/`widgets_settings_save`), and the application combines
them:

```rho
// The tabs, `key|label key,` each — the label is an i18n key.
fn host_settings_tabs() string {
    return "inventory|inventory.settings_tab,scheduler|scheduler.settings_tab,widgets|widgets.settings_tab,"
}

fn host_settings_form(req: Request, tab: string, action: string) string {
    if rho_str_eq(tab, "inventory") { return inventory_settings_form(req, action) }
    if rho_str_eq(tab, "scheduler") { return scheduler_settings_form(req, action) }
    if rho_str_eq(tab, "widgets") { return widgets_settings_form(req, action) }
    return ""
}

fn host_settings_save(req: Request, tab: string, body: string) void {
    if rho_str_eq(tab, "inventory") { inventory_settings_save(body) }
    else if rho_str_eq(tab, "scheduler") { scheduler_settings_save(body) }
    else if rho_str_eq(tab, "widgets") { widgets_settings_save(body) }
}
```

A change of where readings come from is written to the journal.

## The docs page

`GET /docs` shows the application's own `docs/index.md`, read from its assets.

## The pieces an application draws its shell with

| Function | What it draws |
|---|---|
| `appshell_rail_link(req, href, icon, label, extra, phone)` | A place on the rail; `phone` keeps it in a phone's bottom bar. |
| `appshell_rail_tail(req)` | The system group: settings and docs. |
| `appshell_count(n, css)` | A count beside a place. |
| `appshell_middle(req, quick_mode, quick_label)` | The top bar's middle: where readings come from, the mode in force, and a button that starts the application's quick mode (`feeding`, `load-shed`) or ends the mode in force. |
| `appshell_topbar(req, middle)` | The RoboHub top bar: the switcher of the keeper's applications, the middle, and the person signed in (from `X-Rho-Subject`), with sign-out at the keeper. |
| `appshell_toast(message)` | A message shown once the page has loaded. |

The chips are styled by the class `app-chip` (`ok`, `mode`); an application's
layout gives them their look.
