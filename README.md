# RoboHub Orchestrator

**Version 0.4.0**

The orchestrator of the RoboHub ecosystem: a registry of its modules, and the
tools that run over all of them.

The ecosystem is a set of repositories — the interfaces every platform
implements, a platform per family of parts, the runtime and transport the nodes
speak, the devices and drivers they are made of, and the gateway that collects
them. Each is versioned apart and built apart, which is right for the code and
wrong for the questions a person asks about the whole: which modules are there,
which version of each, and does any of it still build.

Those questions are about the ecosystem rather than about a repository, and this
is where they are answered.

## The registry

Every module of the ecosystem is described in `registry/modules/`, one file per
module:

```yaml
name: robohub-avr
role: platform
path: ../robohub-avr
git: https://github.com/RoboHubPlatform/robohub-avr
summary: The 8-bit AVR platform: the interfaces on an ATmega328P, and the Arduino UNO R3.
```

The registry says where a module is and what it is for in the ecosystem. The
module's own manifest is the truth about what it *is*, and the registry does
not repeat it: a registry that repeats what a module already says is a second
copy that drifts.

```sh
robohub registry list          # every module
robohub registry show avr      # one module, in full
robohub registry check         # whether the ecosystem is whole
```

## The registry of tests

Every module keeps a registry of its tests: what they are called, which kind
they are, whether they are run, and the command that runs them. The tests
themselves are in folders — the unit tests in one, the smoke tests in another,
and as many more of either as the project finds useful — and each folder keeps a
registry of its own, so that no registry grows past what it can be read as. The
module's own registry says which registries there are.

```yaml
# tests/registry.yml
name: robohub-avr
registries:
  unit: unit/registry.yml
  smoke: smoke/registry.yml
```

```yaml
# tests/unit/registry.yml
tests:
  the platform's own tests:
    state: enabled
    program: "sh"
    arguments: "tests/unit/run.sh"
```

A test that is not enabled is still a test: it is there, and it is not run. A
run of "all" is the tests that are enabled, and a run of one kind is the tests
of that kind that are enabled.

`robohub test add` registers a test that has been written — and runs it first.
A registry that holds a test which does not work is a registry that will fail a
run for a reason nobody can see, so a test is added only after it has passed.

## Applications

The keeper, which signs people in to every application, installs and supervises
them, has its own repository (`robohub-keeper`, beside this one), and so does
Mesh, which plans and runs gateway deployments (`robohub-mesh`), and the aquarium,
the first modular monolith (`robohub-aquarium`); `applications/energy` is the
power application for a location. The
aquarium is one service on one port, and the inventory module is included into
it and serves `/expenses`, the scheduler serves `/scheduler`, and the widgets
module renders the dashboard cards, on the same router. Energy is the same shape:
one service, reusable modules on its router, and a typed energy and telemetry
store beneath it.

All four applications are keeper-deployed user services. Each has a Logging
settings section — level, text or JSON, a rotating file under
`~/.local/state/robohub/<app>/`, size, retention and stderr — and the keeper's
Applications page links each app to its log. Energy, aquarium and mesh register
with Mesh as clients of their project; subscribed applications receive the
topics they asked for.

## Modules

A module is a reusable application: backend, pages and storage, under
`modules/`. It has no port of its own. The host application includes it and the
module registers its routes on the host's router — the aquarium application is
one service on one port, with the inventory module serving `/expenses`.

`modules/registry.yml` is the installed set; the keeper's `/app-modules` page
lists it, installs and removes modules. A module has no single host: any
application that includes it serves its routes. A module's records and settings live in the workspace of the application
that consumes it (`$ROBOHUB_APP_WORKSPACE/data/app.db`), so two applications
can use the same module without sharing a database.

## Plugins

An application names its plugins and their settings in its own `module.yml`.
`plugins/registry.yml` is the installed set; the manager checks each path on
disk and dispatches by transport. The keeper (`robohub-keeper`) has a `/plugins` page to
install, remove, enable and test them. The alert dispatcher fans out to the
channels an application wires, and the rule engine in `contracts/alert/rule.rho`
adds hysteresis, pending and cooldown windows and a rate limit around a
reading.

The transports live in `providers/` and are ordinary Rho: `log`, `email`
(SMTP or a local outbox), `telegram` and `webhook`. An application that only
needs to send a message can call a provider directly.

## The schemas

The shapes the ecosystem's files are written in are in `schemas/`, one file per
shape and one version per file: `board.v1.json`, `target-spec.v1.json`,
`registry.v1.json` and `suite.v1.json`. They are JSON Schema, so anything else
can check against them too.

The rules themselves are written in Rho, in `src/validate.rho`, so that a
program can keep them. The two are the same contract: what a rule says in one is
what a schema says in the other.

A module manifest is a contract of its own. Its types and the structure each one
is written to live in `robohub-common/contracts/`: a core schema, one schema per
type extending it, and `module-types.json`, which the `rho-robohub` plugin exposes
to `rho module validate`. The toolchain parses the contract and checks the
manifest against it; it does not carry RoboHub's words itself. What the
orchestrator checks here is the ecosystem's own files.

## The tools

The tools are the toolchain's own components, run over each module in turn.
The orchestrator decides *what* to run them over and collects what they said;
the components decide how to run and what their findings mean. A second linter
here would be a linter that reports something else.

```sh
robohub lint                   # static analysis, over every module
robohub lint robohub-avr       # over one
robohub test                   # the tests, over every module
robohub test robohub-avr       # over one
robohub test robohub-avr --unit    # only the unit tests
robohub test robohub-avr --smoke   # only the smoke tests
robohub test list robohub-avr     # what tests the module has
robohub test run robohub-avr NAME # one of them, by its name
robohub test enable robohub-avr NAME   # a test is run
robohub test disable robohub-avr NAME  # a test is not run
robohub docs                   # documentation
```

Each run writes what the tool said to `build/reports/<tool>-<module>.txt`, so
a report survives the run that produced it.

## Running it

The orchestrator is a Rho program, generated as a Go target by the toolchain:

```sh
rho build .            # build/generated/go, and build/robohub
./build/robohub registry list
```

Its tests are run by the toolchain's own runner:

```sh
rho test .
```

## What is shared

The material every repository in the ecosystem needs and none of them should
own is here: the ignore rules, the configuration a CI build resolves, and the
workflow itself. See `shared/`.

## The keeper and Mesh

The keeper is the local dashboard for the ecosystem. Its **Mesh** section plans
and runs gateway deployments: projects, a gateway and its nodes, the
connections between them, and the firmware on their boards. A project is a
folder under `~/.rho/mesh/projects` (or `ROBOHUB_MESH_PROJECTS`); the dashboard
at `/mesh` lists them with their gateway status, and opening one shows the plan
wizard. The full guide is
[Mesh's own guide](https://github.com/RoboHubPlatform/robohub-mesh/blob/main/docs/index.md).

## Telemetry

The telemetry path is one contract from a board to an application. A generated
node firmware publishes a `SensorReading` per fitted module; `robohub-gateway`
normalizes each reading into a sequenced, durable outbox and can require a
bearer token; Mesh polls that outbox into a SQLite store with latest values,
raw history, one-minute and hourly rollups, and per-project retention. Drivers
and board modules describe what they can read in `telemetry_fields` and
`signals`; HTTP devices describe their JSON paths and scales. Aquarium and the
widgets module read the store through the gateway interface and the Mesh provider it binds: a number is
the latest value, a chart is a time-range series, and an output is the source's
action URL. The energy application records generation, storage and grid
readings in the same store and writes power faults into it, so its live SSE
badges and any other telemetry consumer see one truth.

See [Mesh](../robohub-mesh/docs/index.md),
[Aquarium](../robohub-aquarium/docs/index.md),
[Energy](applications/energy/docs/index.md),
[widgets](modules/widgets/docs/index.md),
[robohub-provider-mesh](providers/mesh/README.md),
[robohub-devices](https://github.com/RoboHubPlatform/robohub-devices) and
[robohub-drivers](https://github.com/RoboHubPlatform/robohub-drivers).
