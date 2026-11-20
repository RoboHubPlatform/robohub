# Changelog

All notable changes to this module are recorded here, one section per release.
A module's description says what it is and does not change between releases; this
says what changed, which is what tells two versions of one module apart. The
section for the version being published travels with it, so a registry shows it
against that version.

## [0.1.0] - 2026-10-21

The orchestrator of the RoboHub ecosystem: a registry of its modules, and the
tools that run over all of them.

The registry names every module of the ecosystem, where it is and what it is for,
and each module's own manifest remains the truth about what it is. The
orchestrator reads the manifests it needs and repeats nothing.

The tools are the toolchain's own components — the linter, the test runner and
the documentation generator — run over each module in turn, and what each said
is written to `build/reports/`. The orchestrator decides what to run them over
and collects what they said; the components decide how to run and what their
findings mean.

The material every repository in the ecosystem needs and none of them should own
is here as well: the ignore rules, the configuration a CI build resolves, and
the workflow itself, as a workflow the repositories call rather than a copy
each of them carries.

## [0.2.0] - 2026-11-01

The keeper gains **Mesh**: projects saved in a workspace, a dashboard that
lists them with their gateway status, a plan of the gateway and its nodes, and
network, build/program and verify steps. A project is a folder under
`~/.rho/mesh/projects` (or `ROBOHUB_MESH_PROJECTS`); it can be created, opened,
renamed, described and deleted. Boards and drivers come from the registry's
`capabilities` and `deployment` blocks, and transports from
`robohub-transport`, so a new board or driver is offered without rebuilding the
keeper.

The gateway page, frame history and CSV export, the wall-clock receive time
beside a node's uptime, and the documentation each module now carries with its
release history are part of the ecosystem this release describes.

## [0.3.0] - 2026-11-02

The keeper is an applications registry. A module whose manifest declares an
`application` block is listed at `/applications`, where it can be opened,
started, stopped, added to the keeper's left menu as a sub-item of Applications,
or removed. An application is installed from a git URL or registered from a
folder that already exists; its state lives in `~/.rho/keeper/`.

Mesh moved out of the keeper and into `applications/mesh` as a keeper-hosted
application. It has its own left menu, active-project selection, attached sensor
modules read dynamically from `robohub-drivers/boards`, per-node bus plans with
I2C address and SPI chip-select allocation, and its own documentation page.

## [0.3.1] - 2026-11-02

Mesh models a sensor module as a node of its own (`kind: module`) attached to a
node, instead of a field on the node. Module nodes appear in the plan tree under
the node they extend, are added with **+ Add module** or **+ module**, and are
never built or programmed separately: the node's image carries them. A native
gateway cannot take modules; the controls appear only when the gateway is a real
board.

The module picker is read from `robohub-drivers/boards` on every load and grows
a section for any new board category. The robohub-drivers root manifest now
states the board module contract, so a board added to that checkout is
discoverable without a list elsewhere changing.

## [0.3.2] - 2026-11-02

A plugin system for the applications. An application names its plugins and
settings in its own `module.yml`; `plugins/registry.yml` is the installed set and
the manager confirms each path on disk before using it. The keeper has a
`/plugins` registry to install, remove, enable and test plugins.

The alert dispatcher is the unified alert entry point: it fans out to the
channels named in its targets, each with its own threshold. The transports are
generic Rho providers for a log, e-mail (SMTP or a local outbox with templates),
Telegram and webhooks, and an application can call a provider directly. The
alert rule engine adds hysteresis, pending and cooldown windows and a rolling
rate limit around a reading. Mesh raises an alert when a step fails, through the
same dispatcher.

## [0.3.3] - 2026-11-02

Reusable modules under `modules/`, with `modules/registry.yml` as the
installed set and a keeper `/modules` page to install, remove and open them.
A module has no port of its own: the host application includes it and the module
registers its routes on the host's router.

The aquarium application is the first host: one service on one port, with the
inventory module registering its routes on the aquarium router under
`/expenses`, a scheduler module under `/scheduler` with a chores API, and a widgets module
whose configurable number, chart, button and switch cards make the aquarium's
home page a dashboard. Modules share the host's main SQL database. The aquarium has a stylized background asset
and top/bottom menus.
The inventory module tracks stock on hand, reorder levels, purchases with
categories, quantities, unit prices, stores, dates and comments, a running total,
and SQLite storage through rho-sql. A module keeps its records and settings in
the workspace of the application that consumes it, so two applications using one
module do not share a database; the settings are the `config:` map on the host's
`micro_apps` entry, not anything beside the module.

## [0.3.4] - 2026-11-02

The aquarium framework: equipment and devices, automation rules with an
evaluation and audit trail, water chemistry, operational modes and the event
log. The home page is a dashboard built from configurable widgets, including
buttons and switches whose hooks are called when pressed. Module versions are
independent of the application, and the keeper lists modules without a single
host link. Module forms use the same semi-opaque panels as the aquarium.

## [0.3.5] - 2026-11-04

Keeper authentication and SSO across applications. Keeper is the authorization
server: it holds an ES256 signing key, mints short-lived single-use tickets, and
protects its own admin UI. Aquarium and Mesh verify sessions locally with the
public key, support direct WAN and reverse-proxy origins, and Mesh accepts
signed service JWTs for server-to-server API calls. A robohub-auth plugin and
provider registry make the auth provider selectable.

## [0.4.0] - 2026-11-09

The energy application: one location's generation, storage, grid and loads in
one keeper-hosted service on port 8482. It normalizes solar PV, microinverter
and wind readings, tracks a LiFePO4 bank (SoC, cell window, temperature and the
L51 CAN profile), controls off-grid, on-grid and hybrid modes with load
shedding, generator thresholds, zero export, peak shaving and tariff windows,
evaluates thermal and electrical interlocks, and writes power faults into the
telemetry SQLite/WAL store. Its dashboard is the shared widgets module rather
than a second implementation, and it carries the inventory, scheduler and widget
modules inside the energy shell, with their pages rendered as content in the
host's own menu and layout. The driver seam runs a deterministic stateful
simulator by default and can switch to real-time Mesh telemetry through the same
`mesh-gateway` provider the aquarium uses, without a restart. Simulation mode
publishes simulated gateway sources so widgets preselect them; real-time mode
clears those selections. Applications now register as Mesh clients with their
project, callback and topic subscriptions; Mesh routes published energy faults
and mode changes only to subscribed applications, authenticated by the service
token and a per-client callback secret. Scripted fault injection keeps the smoke
suite runnable without a bench. Every application now has a Logging settings form and a
rotating per-app log, the keeper's Applications page links each app to its log
file, and energy is installed as the same kind of user service as mesh and
aquarium.

Also in this release:

A reactive UI, internationalisation, telemetry and provisioning release.

- Added HTMX and SSE to Aquarium, Keeper and Mesh: widget cards, Mesh tree and
  faults update in place, and pages answer fragments for `HX-Request`.
- Added English and Romanian catalogs, a shared i18n module, flag-based language
  switching, translated application/module navigation, forms and notification
  toasts, and per-locale live widget events.
- Centralized runtime settings in the parent application, with vertical tabs,
  module tab layout, forms-engine settings, plugin alert overrides, and a shared
  settings store.
- Keeper deploys signed staged artifacts with an atomic swap, health check and
  rollback, and manages application services through systemd.
- Mesh telemetry gained WAL maintenance, batched retention, vacuum and storage
  settings, actionable faults with a live HTMX page and API, and gateway polling
  backoff with health reporting.
- Keeper gained one-time node enrollment, a node registry, credential
  verification, rotation and revocation.
- Cross-entity includes use portable bare names, and RoboHub dependencies are
  declared once under `deps.robohub`.

## [0.4.1] - 2026-11-15

Every `let` the code assigned to is declared with `var`, as rho 0.19.0 asks (assigning to a `let` is deprecated there and refused in the next minor release). Nothing else changes.

## [0.4.2] - 2026-11-19

The registry is read from `registry/modules`, not from a list in the program: the list knew 13 modules while the folder had 17, so keeper, mesh, aquarium and energy were never listed, checked, validated, tested, linted or documented. `robohub test` (and `lint` and `docs`) exited 0 when modules failed, so a CI job read a failed run as passing; it exits non-zero now, naming the failures. `lint` and `docs` skipped every module that declares no tests, as `test` rightly does; they run over every module now. `tests/registry_test.rho` was in no suite and its `main` called none of its `test fn`s, so it never ran; it is a suite now, every test is called, and it checks that the registry is the folder (keeper, mesh, aquarium and energy among it). `tests/validate-catches.sh` now checks the one broken entry it writes: with the old list, the twelve entries missing from its scratch registry made the validator fail whatever the entry said. New suite `tests/run-over.sh`.

`schemas/board.v1.json` allows a connector's `position` (an integer from 1): it allowed only `name` and `signal`, with no other property, so the 39 robohub-drivers boards that number their header pins did not match the published schema. The orchestrator's header comment said nothing it runs writes to a module's tree; `test add`, `test enable` and `test disable` rewrite the module's `tests/tests.yml`, and the comment now says so.

Documentation now says what the code does: the history Mesh keeps is 14 days raw, 90 days of minute roll-ups, 1825 of hourly roll-ups and 365 of faults (the reading guide said thirty days, 180 days and five years); the security pages no longer list Energy as a mesh's gateway (it stopped being one on 2026-11-13, ADR-0012), list the gateway's `gateway:<id>:ack` scope beside read and command, and say that the outbox deletes a record once every consumer has acknowledged it and drops the oldest only past `OUTBOX_MAX_ROWS`, not by age; the first-run guide says the access token is made when the sign-in page is first asked for and the signing keys on the first sign-in, not on the keeper's first start. robohub-alert 1.1.2 (a rule fires above its threshold, not when a value reaches it) and appshell 0.2.1 (the rail's system group is settings and docs) are documentation releases.

docsite 0.3.9, appapi 0.2.1, rules 0.2.1, logging 0.2.5, simulator 0.2.4, provider-mesh 0.5.5; scheduler 0.3.2, notifications 0.2.3, settings 0.2.3, forms 0.3.7, inventory 0.4.2, widgets 0.4.2 (already being released today) carry the rest of today's fixes — see their own changelogs.

## [0.4.3] - 2026-11-20

A new plugin, **robohub-zigbee2mqtt** 0.1.0 (ADR-0017, Z2MP-0001..0003): the
Zigbee2MQTT program RoboHub Mesh runs for each Zigbee coordinator, pinned at
2.14.3 (source tarball and container image), the Node.js it needs in
`system_deps` (`^22.2 || ^24`, fetched as Node.js 24.22.3 LTS), and the
configuration template Mesh fills — no secret in it (`!secret` references only),
the network key and PAN ids generated, availability on, frontend and Home
Assistant off, configuration version 5. It is data only and the keeper does not
run it: it declares no `module.kind: integration` (the keeper offers every plugin
of that kind as a service to run) and is not in `plugins/registry.yml` (the
keeper's list of plugins it manages); Mesh finds it through a new registry entry,
`registry/modules/robohub-zigbee2mqtt.yml`, with the new role `plugin`.

`schemas/registry.v1.json` allows the role `plugin`. `robohub validate` checked
a module's manifests, suites and specs in `../<name>`, which for a plugin carried
in this repository is not where it is: it found nothing there and said nothing.
It now looks where the entry's `path` says when a module is there, and in
`../<name>` otherwise, so the plugin's manifest and suite are checked like any
other module's. New suite: the plugin's template check
(`plugins/robohub-zigbee2mqtt/tests/check_template.py`), also declared in the
plugin's own `tests/tests.yml`.

## [0.4.4] - 2026-11-20

Supervision (SYS-0070, ADR-0018), external widgets (SYS-0071, ADR-0019, robohub-feed in the registry) and robohub-node (SYS-0072, ADR-0020): robohub-core, -transport, -telemetry and -freertos live in the robohub-node collection, and their registry entries point there. The validator reads a manifest reached through two entries once, and the docsite builds a module's pages from where its entry says it is, not only from a repository of its name. CI checks out robohub-node and robohub-feed.

## [0.4.5] - 2026-11-20

ADR-0021 (accepted): a node's lifecycle uses each chip's own A/B update, health first, and a separate update key per mesh. robohub-protocol 1.4.0 adds `HEALTH` (PROTO-0007).
