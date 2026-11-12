# The orchestrator

**Version:** 0.4.0

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

## Logging

Every application has one logging policy: level (`trace` to `fatal`), `text` or
`json`, a rotating file under `$XDG_STATE_HOME/robohub/<app>/app.log`, size,
retention and standard error for journald. The keeper's Applications page links
each app to its log, and the shared `modules/logging` module owns the form and
the defaults. Included modules write to the host application log, and the rho
`logemit` port supplies the level filter, formatter and rotation.

## Applications

The ecosystem also has applications: what a person runs rather than what a node
links. They live under `applications/`.

- [Keeper](keeper/) is the dashboard and the registry of the other
  applications. It reads an `application` block from a module's manifest and
  lists, installs, starts, stops and removes the applications on the machine. A
  pinned application is a sub-item of the keeper's Applications menu.
- [Documentation site](docsite/) builds and serves this site.
- [Mesh](mesh/) is a keeper-hosted application of its own. It runs on its own
  port, plans the gateway and its nodes, attaches sensor modules to a node, and
  builds and programs the node images.
- [Aquarium](aquarium/) is the first modular-monolith application: one HTTP
  service on one port, with reusable modules registering their routes on its
  router. It also carries the equipment, automation, chemistry and
  maintenance-mode framework the physical layer will drive.
- [Energy](energy/) is the power application for a location: solar, wind,
  LiFePO4 storage and the utility line normalized into one site reading, with
  off-grid, on-grid and hybrid control, safety interlocks, telemetry/WAL power
  faults and live SSE dashboards. Its driver seam runs a stateful simulator by
  default, so the whole loop can be tested without hardware.
- [Gateway](robohub-gateway/) is the gateway application the earliest
  deployments ran.

A module without an `application` block is not an application — a component or
a documentation site has no listener of its own — which is how the two kinds
stay apart without either naming the other. The `mesh` application was formerly
part of the keeper; it is versioned and built apart now.

## Reactive UI

RoboHub pages are server-rendered and made reactive with HTMX and Server-Sent
Events. The shared HTMX module serves the pinned assets; applications answer
fragments, use one SSE connection per page, and render their own templates.

See [Reactive UI](reactive-ui/) for the conventions, the dual-mode handler
pattern, the event format, and what still needs a small script.

## Languages

Rho pages speak English and Romanian. Catalogs are flat JSON files embedded by
the build, so an off-grid device needs no translation service and no JSON parser
at runtime. `modules/i18n` chooses the language from the `locale` cookie, then
`Accept-Language`, then English, and `{{t "key"}}` translates inside a template.

See [Internationalisation](i18n/) for the catalog format, the switcher, and how
to add a language.

## Modules

**Modules** here means the reusable application modules under `modules/`: they
have both backend and pages and are included by an application. A module has no
port of its own; the host application includes it and the module registers its
routes on the host's router.

The ecosystem repositories are not modules. They are grouped by the `module.type`
in their manifest — runtime, middleware, interfaces, platform, collection — so
Freertos sits under middleware and Core under runtime, and neither is mixed into
this section.

The allowed types and the structure each one is written to are the ecosystem's
own contract, in `robohub-common/contracts/`: a core module schema, one schema
per type that extends it, and the `module-types.json` the Rho toolchain loads
through the `rho-robohub` plugin. Rho does not carry this ecosystem's words; a
project whose platform is recognized gets them from the plugin. Every manifest
also carries a `module.id`, prefixed by the repository and path it belongs to;
telemetry sources are keyed on it so a shared name is not a shared identity.

A device is a network integration from `robohub-devices` — a Shelly plug, an
inverter — and Mesh shows it as a device node attached to a gateway or relay. It
is not built; the parent node carries it, and an HTTP device can be polled and
switched from its node page. A device is a module of type `device`, not a
`driver`: a driver reaches a part through the HAL, and a device reaches the
equipment that part is in, often over a protocol of the equipment's own.

`modules/registry.yml` is the installed set, and the keeper's `/app-modules` page
installs, removes and lists modules. A module has no single host: any application
that includes it serves its routes.
A module keeps its records in the workspace of the application that consumes it,
under `$ROBOHUB_APP_WORKSPACE/data/app.db`, so the same module in two
applications has two databases.

The modules are:

- [Logging](logging/) — the shared logging policy for applications and modules.
- [Inventory & expenses](inventory/) — stock on hand, reorder levels, purchases
  with categories, quantities, unit prices, stores, dates and comments;
- [Scheduler](scheduler/) — interval, cron, one-time and usage-based chores with
  due and overdue states, completion notes, snoozing and a JSON API;
- [Widgets](widgets/) — number, chart, button and switch cards for the host
  application's dashboard, with a manager and an API.

All of them store their tables in the host's main SQL database and their
settings in the host application.

## Alerts

An application raises an alert through the alert interface, `robohub-alert`, and
the alert reaches every channel the application binds. A channel is a provider
of the interface: a module that lists `robohub.alert` under `implements` and
exports the interface's `send`. The application declares the interface and the
providers it uses under `deps`, imports the interface, and binds the providers
in its `module.yml`:

```yaml
deps:
  robohub:
    robohub-alert: ">=1.0.0"
    robohub-provider-log: ">=0.2.0"
    robohub-provider-email: ">=0.2.0"

bind:
  robohub.alert:
    providers: [robohub-provider-log, robohub-provider-email]
    config:
      robohub-provider-log:
        path: "~/.rho/myapp/alerts.log"
      robohub-provider-email:
        enabled: "false"
        to_address: "ops@robohub.internal"
        severity_threshold: ERROR
```

```rho
import robohub.alert

let sent: u32 = alert.raise("WARNING", "The tank is above 28 C.", "node=1")
```

Only the bound providers are compiled into the application. A channel receives
an alert when it is enabled and the alert meets its `severity_threshold`. The
settings in `bind:` are defaults: an application's Settings page changes them on
a running installation through `alert.configure`, which writes the
application's `bind.conf`, so a new e-mail address does not need a rebuild.

The channels are:

- [Local log](robohub-provider-log/) — appends to a file, rotating it at 1 MiB;
- [E-mail](robohub-provider-email/) — SMTP or a local outbox, with templates;
- [Telegram](robohub-provider-telegram/) — a chat through the bot API;
- [Webhook](robohub-provider-webhook/) — a generic HTTP endpoint.

The keeper's `/plugins` page lists the channels the keeper binds, switches one
off and sends a test alert through it.

### Alert rules

`contracts/alert/src/rule.rho` is the state machine an application runs before
it raises an alert: hysteresis, a pending window that ignores a momentary spike,
a cooldown after an alert clears, and a rolling rate limit. An application
evaluates a sample and, when the result says it fired, raises the alert. The
rule knows nothing about e-mail or chat; the channels own delivery.

## Plugins

A plugin is a Rho module under `plugins/` that extends an application at run
time: `robohub-auth` signs a person in, `mesh-gateway` reaches a mesh's nodes.
Its manifest says what kind it is (`module.plugin_kind`). The installed set is
`plugins/registry.yml`; a folder that is not in it is not loaded, and an entry
whose folder is gone is shown as missing. The keeper's `/plugins` page lists the
set, installs and removes plugins, and toggles the keeper's own.

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

The role is the ecosystem's own word for what a module is: `interfaces` for the
contracts, `platform` for a family of parts, `runtime` for what a node runs,
`collection` for a set of things, `middleware` for what a platform is built
against, and `application` for what a person runs.

## The commands

```sh
robohub registry list          # every module
robohub registry show avr      # one module, in full
robohub registry check         # whether the ecosystem is whole
robohub validate               # whether the ecosystem's files match the schemas
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

A module that declares no tests is not a module whose tests failed: it is
reported as having none, because a run over an ecosystem that says some of it
has not been written yet is not a run that is broken.

Every command is a report about the ecosystem and nothing else. Nothing here
changes a module, and nothing here writes to a module's tree: a tool that
changes what it measures is not a tool that measures.

`registry check` is the one that fails. A registry that names a module that is
not there sends a reader looking for something that does not exist, and a
module that is not named is a module nobody is told about — so the check says
what is missing and does not succeed.

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

The tools are the toolchain's own components — `rho lint`, `rho test` and
`rho doc` — run over each module in turn. The orchestrator decides *what* to
run them over and collects what they said; the components decide how to run and
what their findings mean. A second linter here would be a linter that reports
something else, and a run that says "no findings" from a tool that never ran is
worse than a run that failed.

Each run writes what the tool said to `build/reports/<tool>-<module>.txt`, so a
report survives the run that produced it.

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
own lives here, in `shared/`:

| What | Where |
|------|-------|
| The host-test runner every module uses | `shared/tests/run-host-tests.sh` |
| The configuration a CI build resolves | `shared/ci/project.conf` |
| The workflow every repository calls | `.github/workflows/robohub-ci.yml` (at this repository's root, where a called workflow has to be) |

A repository takes what it needs from here and says where it came from, rather
than carrying a copy that drifts. The host-test runner is the clearest case:
`robohub-devices` and `robohub-drivers` each carried a copy of the same build —
the same compiler, the same warnings, the same include paths, the same generated
namespace — and had already begun to differ. The runner is here now, and what
is left in each repository is the part that is its own: the headers it
publishes and the suites it runs, in `tests/host-tests.plan`.

## The keeper and Mesh

The keeper is the local dashboard for the ecosystem. Its **Mesh** section plans
and runs gateway deployments: projects, a gateway and its nodes, the
connections between them, and the firmware on their boards. A project is a
folder under `~/.rho/mesh/projects` (or `ROBOHUB_MESH_PROJECTS`); the dashboard
at `/mesh` lists them with their gateway status, and opening one shows the plan
wizard. The full guide is
[the keeper's Mesh guide](https://github.com/RoboHubPlatform/robohub/blob/main/applications/keeper/docs/mesh.md).


## Authentication

RoboHub applications use Keeper as a local SSO authorization server. Keeper holds
the ES256 signing key and mints short-lived, single-use login tickets. Each
application verifies tickets locally with the public key, keeps its own session,
and can run on a direct WAN address or behind a reverse proxy. Server-to-server
calls use a signed service JWT, so Mesh APIs stay protected while Aquarium still
reads and drives them. The `robohub-auth` plugin names the provider; the gateway
and session details live under `contracts/` and `providers/`.
