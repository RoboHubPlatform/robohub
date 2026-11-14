# Simulator

Simulated devices behind the gateway interface. The module implements
`robohub.gateway` itself, so an application binds it beside the Mesh provider and
Settings → Gateway chooses which one answers; inventory, rules, widgets and the
application cannot tell the difference. What the devices are is the
application's `presets/sim.yml`; how they behave is the models here.

```yaml
devices:
  sim-heater-plug:
    label: Heater plug
    sources:
      switch: { model: state, initial: off }
      power:  { model: when, of: switch, on: 200, off: 0, noise: 3, unit: W }
  sim-probe:
    label: Water probe
    sources:
      temperature:
        model: thermal
        initial: 24.8
        ambient: 22
        heater: sim-heater-plug.switch
        rate: 0.6
        cool: 0.15
        unit: °C
```

(Written in block style in a real file; the YAML reader takes block maps.)

A device may name its `board:`, which is the node it hangs off in the tree
`nodes()` draws. A source's id is `<device>.<signal>` — `sim-probe.temperature` — the shape Mesh's
stable ids have.

## Models

| Model | Settings | Behaves |
|---|---|---|
| `state` | `initial` | a switch (or a set value): changed only by `action` |
| `constant` | `value`, `noise` | a value, with noise |
| `noise` | `base`, `noise` | a value wandering around a base |
| `when` | `of`, `on`, `off`, `noise` | `on` while the source `of` names is on, `off` otherwise: a plug's watts |
| `day` | `peak`, `from`, `to`, `noise` | a half sine from `from` to `to` (HH:MM), peaking halfway: the sun, a light's ramp |
| `thermal` | `initial`, `ambient`, `heater`, `rate`, `cool`, `noise` | rises `rate` per hour while `heater` is on, otherwise drifts to `ambient` by `cool` of the difference per hour |
| `sum` | `of` | `a + b - c`: adds and subtracts other sources, a balance |
| `integrator` | `initial`, `of`, `capacity` | a battery's state of charge in percent, from a power source in watts and a capacity in watt-hours |

`of` and `heater` name a signal of the same device (`switch`) or a full id.

## How an application uses it

The simulator is a gateway provider, so the application imports it rather than
including it. Add it to `deps` (`robohub: simulator: ">=0.1.0"`) and list it
beside the Mesh provider under `robohub.gateway` in the application's `bind:`
block:

```yaml
bind:
  robohub.gateway:
    providers:
      - robohub-provider-mesh
      - simulator
    config:
      robohub-provider-mesh:
        url: "http://127.0.0.1:8478"
        project: "default"
        transport: auto
      simulator:
        enabled: "false"
```

`enabled: "false"` keeps the simulator from answering until someone chooses it:
the settings page's gateway tab (see {ref}`appshell/index`) calls
`gateway.choose`, which enables one bound provider and disables the others in
the application's `bind.conf`. The application then reads its presets at start and moves the
simulation on from its background work:

```rho
import robohub.simulator

simulator.presets(rho_asset("aquarium", "presets/sim.yml"))   // at start
simulator.tick()                                               // every few seconds, while it is the gateway
```

A source moves at most once a second, however often `tick()` is called.

## Data it keeps

Its state — the sources, their values, a week of history and the files its live
feed is followed into — is kept in files under the application's workspace
(`data/simulator/`), because a gateway provider is imported, not included, and
does not share the application's tables. Values are kept in thousandths (24.5 °C
is 24500), and each tick writes a line to every followed feed in Mesh's own
stream format, so what reads the feed cannot tell it from a mesh. The module
declares no settings of its own; `enabled` above is the binding's.
