# Changelog

All notable changes to this module are recorded here, one section per release.
A module's description says what it is and does not change between releases; this
says what changed, which is what tells two versions of one module apart. The
section for the version being published travels with it, so a registry shows it
against that version.

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
