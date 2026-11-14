# RoboHub

Home, aquarium and energy automation that runs on your own machine, built with
[Rho](https://rho-lang.org).

- **The keeper** (`robohub-keeper`) is the front door and the supervisor: it
  listens on `127.0.0.1:19090`, signs people in, installs the applications, runs
  each as a systemd user unit and serves them under its own origin at
  `/app/<name>/`.
- **The applications** — Mesh (`robohub-mesh`), Aquarium (`robohub-aquarium`),
  Energy (`robohub-energy`) — are each one HTTP service built mostly from the
  shared modules in this repository.
- **Mesh** plans and runs the gateways, boards and devices, and keeps every
  reading; the gateway (`robohub-gateway`) collects authenticated frames from the
  boards; the firmware lives in the platform, driver and device repositories.

The documentation for all of it is built into one site from this repository:
start with [docs/index.md](docs/index.md), and
[docs/start/install.md](docs/start/install.md) to run it.

## What is in this repository

| Folder | What it holds |
|---|---|
| `modules/` | The shared modules applications include: `appshell`, `inventory`, `rules`, `scheduler`, `widgets`, `journal`, `appapi`, `forms`, `i18n`, `settings`, `logging`, `ui`, `htmx`, `notifications`, `simulator` |
| `contracts/` | The interfaces applications import: `robohub.gateway`, `robohub.bus`, `robohub.alert` |
| `providers/` | Their providers: Mesh and MQTT, and e-mail, Telegram, webhook and log for alerts |
| `plugins/` | What the keeper runs or loads: `robohub-auth` (sign-in), `robohub-mqtt` (the Mosquitto broker) |
| `protocol/` | The wire protocol the boards and the gateway share |
| `registry/modules/` | One file per repository of the ecosystem: where it is and what it is for |
| `schemas/` | JSON Schemas for the ecosystem's files (boards, target specs, the registry, test suites) |
| `shared/` | The host-test runner and CI configuration every repository uses |
| `applications/docsite` | The program that builds the documentation site |
| `docs/` | The ecosystem's own pages: overview, getting started, architecture, writing an application |
| `src/` | The `robohub` command |

## The `robohub` command

A report over the whole ecosystem, using the toolchain's own components; it
changes no module.

```sh
rho build .                     # builds ./build/robohub
./build/robohub registry list   # every repository
./build/robohub registry check  # whether the registry and the checkouts agree; fails when not
./build/robohub validate        # whether the ecosystem's files match the schemas
./build/robohub lint [module]   # rho lint, over every module or one
./build/robohub test [module]   # rho test, over every module or one (--unit, --smoke)
./build/robohub docs            # rho doc, over every module
./build/robohub keeper [port]   # runs a built keeper on 127.0.0.1:19090
```

Each run writes what the tool said to `build/reports/<tool>-<module>.txt`. The
command's own tests are `rho test .`.

## The documentation site

```sh
rho build applications/docsite
./applications/docsite/build/docsite      # writes build/site/
```

See [applications/docsite/README.md](applications/docsite/README.md) for serving
it and building its container image.

## License

MIT
