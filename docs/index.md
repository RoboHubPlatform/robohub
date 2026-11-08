# The orchestrator

**Version:** 0.3.4

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

A device is a network integration from `robohub-devices` — a Shelly plug, an
inverter — and Mesh shows it as a device node attached to a gateway or relay. It
is not built; the parent node carries it, and an HTTP device can be polled and
switched from its node page.

`modules/registry.yml` is the installed set, and the keeper's `/app-modules` page
installs, removes and lists modules. A module has no single host: any application
that includes it serves its routes.
A module keeps its records in the workspace of the application that consumes it,
under `$ROBOHUB_APP_WORKSPACE/data/app.db`, so the same module in two
applications has two databases.

The modules are:

- [Inventory & expenses](inventory/) — stock on hand, reorder levels, purchases
  with categories, quantities, unit prices, stores, dates and comments;
- [Scheduler](scheduler/) — interval, cron, one-time and usage-based chores with
  due and overdue states, completion notes, snoozing and a JSON API;
- [Widgets](widgets/) — number, chart, button and switch cards for the host
  application's dashboard, with a manager and an API.

All of them store their tables in the host's main SQL database and their
settings in the host application.

## Plugins

An application's `module.yml` names the plugins it uses and their settings:

```yaml
plugins:
  - name: alert-dispatcher
    enabled: true
    config:
      targets: "alert-log,email-alert,telegram-notifier"
      severity_threshold: INFO
  - name: email-alert
    enabled: false
    config:
      provider: local
      to_address: "ops@robohub.internal"
      subject_template: "[RoboHub {app}] {level}: {rule}"
```

A plugin is a Rho module under `plugins/` whose manifest has a `plugin:` block;
that block, not the module type, is what makes it a plugin. The installed set is
`plugins/registry.yml`. The manager reads it at load time, confirms each path
still has a `module.yml`, and dispatches by the transport the plugin manifest
names. A folder that is not in the registry is not loaded; an
entry whose folder is gone is shown as missing. The keeper's `/plugins` page
lists the registry, installs and removes plugins, toggles the keeper's own set
and sends a test alert.

The plugins are:

- [Dispatcher](alert-dispatcher/) — fans an alert out to the channels in its
  target list;
- [Local log](alert-log/) — appends to a file;
- [E-mail](email-alert/) — SMTP or a local outbox, with templates;
- [Telegram](telegram-notifier/) — a chat through the bot API;
- [Webhook](webhook-alert/) — a generic HTTP endpoint.

The transports are generic Rho code under `providers/`: `log`, `email`,
`telegram` and `webhook`. An application can call a provider directly for a
message that is not an alert. A plugin that needs a transport of its own names a
`plugin.command`, a Rho program the manager runs with a request file; adding it
does not rebuild the manager.

### Alert rules

`contracts/alert/rule.rho` is the state machine above the dispatcher: hysteresis,
a pending window that ignores a momentary spike, a cooldown after an alert
clears, and a rolling rate limit. An application evaluates a sample and, when
the result says it fired, hands the message to the alert dispatcher. The rule
knows nothing about e-mail or chat; the dispatcher and its channels own
delivery.

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

The manifests are the toolchain's own business — `rho module validate` is the
authority on what a manifest may say, and it is what the toolchain reads. What
the orchestrator checks is the ecosystem's own files.

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
| The workflow itself | `shared/.github/workflows/robohub-ci.yml` |

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
