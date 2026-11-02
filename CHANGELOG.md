# Changelog

All notable changes to this module are recorded here, one section per release.
A module's description says what it is and does not change between releases; this
says what changed, which is what tells two versions of one module apart. The
section for the version being published travels with it, so a registry shows it
against that version.

## [0.3.3] - 2026-11-02

Reusable modules under `modules/`, with `modules/registry.yml` as the
installed set and a keeper `/modules` page to install, remove and open them.
A module has no port of its own: the host application includes it and the module
registers its routes on the host's router.

The aquarium application is the first host: one service on one port, with the
inventory module registering its routes on the aquarium router under
`/expenses`, and a scheduler module under `/scheduler` with a chores API. Modules
share the host's main SQL database. The aquarium has a stylized background asset
and top/bottom menus.
The inventory module tracks stock on hand, reorder levels, purchases with
categories, quantities, unit prices, stores, dates and comments, a running total,
and SQLite storage through rho-sql. A module keeps its records and settings in
the workspace of the application that consumes it, so two applications using one
module do not share a database; the settings are the `config:` map on the host's
`micro_apps` entry, not anything beside the module.

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
