# RoboHub

RoboHub is home, aquarium and energy automation that runs on your own machine.
Sensors and switches report through a gateway you run; the applications that
read them, keep their history and act on them run on your computer, under your
account, with no cloud service in between. It is written in
[Rho](https://rho-lang.org), and every part of it is a Rho module.

## The parts

| Part | What it does |
|---|---|
| **The keeper** | The front door and the supervisor. It listens on `127.0.0.1:19090`, signs people in (admin, operator and viewer roles), installs the applications, runs each as a systemd user unit from a release, and serves them under its own origin at `/app/<name>/`. |
| **Applications** | What a person uses. **Mesh** manages gateways and the boards and devices behind them; **Aquarium** looks after tanks, water, dosing, livestock and equipment; **Energy** works out a site's balance of solar, storage and grid, and applies a policy with load shedding. |
| **Shared modules** | What every application needs and none should write again: the shell and settings pages, inventory and equipment, the scheduler, rules and modes, the journal, dashboard widgets, forms, languages, logging. An application includes them, and they register their routes on its router. |
| **Interfaces and providers** | An application reaches the outside world only through an interface — `robohub.gateway` for readings and switches, `robohub.bus` for MQTT, `robohub.alert` for alerts — and binds providers to it in its `module.yml`: Mesh or the simulator for the gateway, the keeper's Mosquitto broker for the bus, e-mail, Telegram, a webhook or a log file for alerts. |
| **Mesh, gateways and devices** | A gateway collects authenticated frames from boards over serial, USB or Wi-Fi and polls network devices; Mesh plans the tree, builds and flashes the boards, and keeps every reading in one telemetry store. A gateway can report through another one (relay and uplink), so one Mesh runs several linked meshes. |
| **Firmware** | The device side: the board platforms (Pico, ESP32, STM32, AVR, Linux), FreeRTOS, the runtime, transport and telemetry a node runs, and the drivers and device integrations. |

{ref}`architecture/index` shows how the parts connect, and
{ref}`architecture/reading` follows one reading from a sensor to a widget.

## Where to start

- **Running it:** {ref}`start/install`, then {ref}`start/first-run`,
  {ref}`start/applications` and {ref}`start/gateway`.
- **Using an application:** {ref}`keeper/index`, {ref}`mesh/index`,
  {ref}`aquarium/index`, {ref}`energy/index`.
- **Writing an application:** {ref}`build/host-application`, then the shared
  modules under *Build an application*.
- **Connecting hardware:** {ref}`robohub-gateway/index` and the parts under
  *Devices & firmware*.

## Where the code is

Each part has its own repository, versioned and released apart. This one,
`robohub`, holds what they share: the shared modules (`modules/`), the
interfaces (`contracts/`) and their providers (`providers/`), the integrations
the keeper runs (`plugins/`), the wire protocol (`protocol/`), the registry of
the ecosystem's repositories (`registry/modules/`), the schemas, and the
`robohub` command, which runs the toolchain's lint, tests and documentation over
all of them:

```sh
rho build .                     # builds ./build/robohub
./build/robohub registry list   # every repository of the ecosystem
./build/robohub registry check  # whether the registry and the checkouts agree
./build/robohub test            # every module's tests
./build/robohub keeper          # runs a built keeper on 127.0.0.1:19090
```

This site is built from all of them by `applications/docsite`.
