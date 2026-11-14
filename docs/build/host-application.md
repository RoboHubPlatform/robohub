# Writing a host application

Aquarium and Energy are mostly the same program: one HTTP service whose pages,
inventory, schedule, rules, journal and dashboard come from the shared modules,
with a small domain of its own on top. An application that does the same is a
**host application**: it includes the modules, declares them in its manifest,
binds the interfaces they use, and defines the `host_*` functions they call.

This page is what a host has to provide. Each module's own page says what it
offers, and ends with a generated *Reference* of its exports, routes and the
hooks it calls.

## The shape of one

```text
greenhouse/
  module.yml          what it is, what it includes, what it binds
  project.yml         the go-server target: middleware, templates, locales
  src/main.rho        includes, routes, init() and background()
  src/storage.rho     the runtime functions it declares (copy Aquarium's)
  src/greenhouse/     its own domain, and shell.rho with the host hooks
  db/schema.sql       its own tables only; the modules bring theirs
  presets/            what the modules are seeded with
  templates/layouts/layout.html
  locales/en.json
  docs/index.md       the page /docs shows
```

## module.yml

```yaml
module:
  name: greenhouse
  id: robohub.app.greenhouse
  type: rho
  version: 0.1.0
  kind: keeper-hosted          # the keeper can install, start and proxy it
  title: Greenhouse
  route: /                     # its first page
  port: "8490"                 # its loopback port; the keeper picks another if taken
  command: greenhouse          # the program rho build makes

platform: robohub
main: src/main.rho

build:
  language: go
  targets: [go-server]

# The modules' tables are generated in beside the application's own.
requires:
  - name: rho/sqlite
sql:
  driver: rho-sql-sqlite
  schema: db/schema.sql
  out: src/db

deps:
  rho-log: ">=0.1.0"
  rho-sql: ">=0.1.0"
  robohub:
    ui: ">=0.1.0"
    htmx: ">=0.1.0"
    i18n: ">=0.4.0"
    settings: ">=0.2.0"
    forms: ">=0.3.0"
    notifications: ">=0.1.0"
    logging: ">=0.2.0"
    inventory: ">=0.3.0"
    journal: ">=0.1.0"
    rules: ">=0.1.0"
    widgets: ">=0.2.6"
    appshell: ">=0.2.0"
    simulator: ">=0.1.0"
    robohub-auth: ">=0.1.0"
    robohub-gateway: ">=1.1.0"          # the interface
    robohub-provider-mesh: ">=0.4.0"    # a provider for it

# The module instances: where each is mounted. The keeper reads this list to know
# which application serves a module's routes.
modules:
  - {name: inventory, route: /expenses, enabled: true}
  - {name: journal,   route: /journal,  enabled: true}
  - {name: rules,     route: /rules,    enabled: true}
  - {name: widgets,   route: /widgets,  enabled: true}

# How a person is signed in: by the keeper.
plugins:
  - name: robohub-auth
    enabled: true
    config:
      issuer: keeper
      mode: direct
      login_url: "http://127.0.0.1:19090/auth/login"

# Each interface the modules import, bound to the providers that answer it. The
# config is the default; Settings → Gateway changes it on a running installation.
bind:
  robohub.gateway:
    providers: [robohub-provider-mesh, simulator]
    config:
      robohub-provider-mesh:
        url: "http://127.0.0.1:8478"
        project: "default"
        transport: auto
      simulator:
        enabled: "false"

deploy:
  port: 8490
  service: greenhouse
  calls: [mesh]               # the keeper registers it as Mesh's client

assets:                       # embedded at build time
  - presets
  - docs/index.md
```

What each block is for:

| Block | Why the host declares it |
|---|---|
| `deps` → `robohub` | every shared module, interface and provider it includes, by version |
| `modules` | the route each module instance is mounted on, and whether it is on |
| `bind` | which provider answers each interface the modules import; only those are compiled in |
| `requires` / `sql` | the SQL port the modules' tables are generated into |
| `deploy.calls` | the services it calls, so the keeper starts it with a credential for them and their addresses |
| `assets` | the presets and the docs page, read with `rho_asset` |

Add `robohub.alert` to `bind:` (with `robohub-alert` and the providers under
`deps`) for the rules' alerts to reach e-mail, Telegram, a webhook or a log, and
`robohub.bus` with a `bus:` block for MQTT ({ref}`robohub-mqtt/index`).

## project.yml

```yaml
targets:
  - id: go-server
    middleware:
      - name: same_origin        # refuse forms posted from another origin
      - name: auth
        options:
          issuer: keeper
          skip_paths: "/healthz,/auth/login,/assets,/assets/,/i18n,/auth/callback,/static,/ui,/docs"
    default_locale: en
    locales:
      - {locale: en, file: locales/en.json}
    templates:
      - dir: templates
```

## src/main.rho

Modules are included by name, a module after the ones it reads — rules after
inventory and journal — and the domain after the modules:

```rho
module greenhouse

include "settings"
include "i18n"
include "ui"
include "storage.rho"
include "db/models.rho"
include "db/queries.rho"
include "inventory"
include "widgets"
include "journal"
include "rules"
include "appshell"
include "logging"
include "htmx"
include "greenhouse/shell.rho"

import std.sql
import std.web.http
import std.web.template
import rho.log
import robohub.gateway
import robohub.simulator

route GET "/" => greenhouse_home

fn greenhouse_home(req: Request) Response {
    return host_shell(req, "Greenhouse", "<div class=\"ph\"><h1>Greenhouse</h1></div>", "")
}

// init seeds what the presets say.
fn init() void {
    log_config_apply("greenhouse")
    ignore_u32(inventory_presets(rho_asset("greenhouse", "presets/inventory.yml")))
    ignore_u32(rules_presets(rho_asset("greenhouse", "presets/rules.yml")))
    ignore_u32(simulator.presets(rho_asset("greenhouse", "presets/sim.yml")))
}

// background follows the live feed, refreshes the dashboard and runs the rules.
fn background() void {
    var ticks: u32 = 0
    while true {
        ticks = ticks + 1
        if ticks % 10 == 5 && rho_str_eq(gateway.provider(), "simulator") {
            ignore_u32(simulator.tick())
        }
        let reading: bool = widgets_live_changed()
        if reading {
            ignore_u32(widgets_refresh_all())
        }
        if reading || ticks % 10 == 0 {
            ignore_u32(rules_tick())
        }
        rho_sleep_ms(500)
    }
}
```

## The host hooks

A module calls these and does not define them; the application does. A build
that includes a module without its hooks fails on the missing function.

| Hook | Called by | What it answers |
|---|---|---|
| `host_app() string` | appshell | the application's name (`aquarium`): which assets `/docs` reads, which logger the logging tab configures |
| `host_app_title() string` | appshell | how the top bar names it (`Aquarium`) |
| `host_shell(req, title, body, scripts) Response` | appshell, inventory, scheduler, widgets, journal, rules | a whole page: the module's content inside the application's layout, top bar and rail |
| `host_settings_tabs() string` | appshell | the tabs the application adds to `/settings`, `key\|label-key,` each |
| `host_settings_form(req, tab, action) string` | appshell | the form of one of those tabs — usually the module's own `*_settings_form` |
| `host_settings_save(req, tab, body)` | appshell | saves it — usually the module's own `*_settings_save` |
| `host_devices_sections(req) string` | inventory | the Devices page's sections, `key\|label` per line |
| `host_devices_roles(req, section) string` | inventory | a section's roles, `handle\|label\|category\|capabilities\|hint` per line |
| `host_devices_categories(req, section) string` | inventory | the categories a section lists and adds to, comma-separated, or `""` |
| `host_devices_query(req) string` | inventory | what the page keeps in its address across a save (`tank=2`), or `""` |
| `host_devices_intro(req) string` | inventory | what is shown above the sections, or `""` |
| `host_devices_value(capability, text) string` | inventory | a reading as the page shows it (`1.2 kW`) |
| `host_devices_added(id, category)` | inventory | what follows an item added on the page |
| `host_devices_changed(handle, what)` | inventory | a mapping changed; the journal is the usual place |
| `rules_host_value(ref) string` | rules | the application's own values a rule may name, `""` for any it does not know |

The implementations to read are `robohub-aquarium/src/aquarium/shell.rho` and
`devices.rho`, and `robohub-energy/src/energy/shell.rho` and `devices.rho`.

### A minimal shell.rho

```rho
module greenhouse

fn host_app() string {
    return "greenhouse"
}

fn host_app_title() string {
    return "Greenhouse"
}

// The settings tabs the modules add to appshell's page.
fn host_settings_tabs() string {
    return "inventory|inventory.settings_tab,widgets|widgets.settings_tab,"
}

fn host_settings_form(req: Request, tab: string, action: string) string {
    if rho_str_eq(tab, "inventory") { return inventory_settings_form(req, action) }
    if rho_str_eq(tab, "widgets") { return widgets_settings_form(req, action) }
    return ""
}

fn host_settings_save(req: Request, tab: string, body: string) void {
    if rho_str_eq(tab, "inventory") { inventory_settings_save(body) }
    else if rho_str_eq(tab, "widgets") { widgets_settings_save(body) }
}

// The rail: places, then appshell's settings and docs.
fn gh_rail(req: Request) string {
    return appshell_rail_link(req, "/", "◉", "Overview", "", true) +
        appshell_rail_link(req, "/expenses", "▤", "Inventory", "", false) +
        appshell_rail_link(req, "/rules", "⚙", "Rules", "", true) +
        appshell_rail_link(req, "/journal", "☰", "Journal", appshell_count(journal_open_count(), ""), false) +
        appshell_rail_link(req, "/widgets", "▦", "Dashboard", "", false) +
        appshell_rail_tail(req)
}

// Every page, the application's and the modules', is drawn here.
fn host_shell(req: Request, title: string, body: string, scripts: string) Response {
    let document: string = template_fill(template_get("layout"),
        vars("title", title) +
        vars("theme", ui_theme(req)) +
        vars("ui_head", ui_head()) +
        vars("htmx", htmx_head()) +
        i18n_vars(req) +
        vars("topbar", appshell_topbar(req, appshell_middle(req, "", ""))) +
        vars("nav", gh_rail(req)) +
        vars("body", body + scripts) +
        vars("notifications", notification_embed()) +
        vars("forms_style", forms_style()) +
        vars("widgets_style", widgets_style()))
    return html(status_ok(), document)
}

// One section of roles, from the application's presets.
fn host_devices_sections(req: Request) string {
    return "beds|"
}

fn host_devices_roles(req: Request, section: string) string {
    return "heater|Heater|heating|switch, temperature?|the bed's heating mat\n" +
        "fan|Fan|ventilation|switch|the vent fan\n"
}

fn host_devices_categories(req: Request, section: string) string { return "" }
fn host_devices_query(req: Request) string { return "" }
fn host_devices_intro(req: Request) string { return "" }
fn host_devices_value(capability: string, text: string) string { return text }
fn host_devices_added(id: u32, category: string) void {}

fn host_devices_changed(handle: string, what: string) void {
    journal_info("device", handle, "person", what)
}

// Nothing of its own for a rule to name yet.
fn rules_host_value(ref: string) string {
    return ""
}
```

The layout template receives `title`, `theme`, `ui_head`, `htmx`, the i18n
variables, `topbar`, `nav`, `body`, `notifications`, `forms_style` and
`widgets_style`; Aquarium's `templates/layouts/layout.html` is the one to start
from.

## Presets

A module seeds what it keeps from the application's presets, called from
`init()`:

| File | Read by | Seeds |
|---|---|---|
| `presets/inventory.yml` | `inventory_presets` | categories |
| `presets/rules.yml` | `rules_presets` | rules and modes |
| `presets/schedule.yml` | `scheduler_presets` | chores |
| `presets/api.yml` | `appapi_presets` | the values the application offers |
| `presets/sim.yml` | `simulator.presets` | the simulated devices |

A preset is added when it is missing and kept as the presets say; one a person
changed is theirs and is left alone.

## Build and run it

```sh
rho build greenhouse
```

Then install it from the keeper as a folder ({ref}`start/applications`): the
keeper writes its unit, gives it a port, a workspace and a client credential for
Mesh, and serves it at `/app/greenhouse/`. Its pages update live as
{ref}`build/reactive-ui` describes.
