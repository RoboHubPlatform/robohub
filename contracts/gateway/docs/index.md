# robohub-gateway

The gateway interface. An application asks for a mesh's projects, sources,
readings and live stream, and switches its outputs; the provider it binds
answers. A gateway is one place, so the first enabled provider bound is the one
asked. The provider today is `robohub-provider-mesh`, and the simulator module
answers the same calls when an application runs without devices.

```yaml
deps:
  robohub:
    robohub-gateway: ">=1.2.0"
    robohub-provider-mesh: ">=0.5.0"
    simulator: ">=0.1.0"
bind:
  robohub.gateway:
    providers: [robohub-provider-mesh, simulator]
    config:
      robohub-provider-mesh:
        project: "default"
        transport: auto
      simulator:
        enabled: "false"
```

This is a different module from the gateway firmware and server
({ref}`robohub-gateway/index`): the interface is what an application calls, and
the Mesh provider reaches the gateway through Mesh, never directly.

## Choosing the provider

The provider that answers is the first bound one whose `enabled` setting is not
`"false"`. `choose(name)` makes one bound provider the one that answers by
writing `enabled` for every bound provider into the application's `bind.conf`
(`<provider>.<key>=value` lines in its workspace, which win over the `bind:`
values), so the choice survives a restart and needs no rebuild. The gateway tab
of `appshell`'s settings page is that choice, with the Mesh provider's `project`
and `transport` beside it (see {ref}`appshell/index`).

An application rarely calls the gateway for a device by name: the inventory binds
an item's capabilities to the gateway's sources, and the rules, the dashboard
and the pages name the item (`heater.switch`).

## What an application calls

| Function | What it does |
|---|---|
| `provider()`, `providers()` | the provider that answers; every bound one, one per line |
| `choose(name)` | makes one bound provider the one that answers |
| `config(key)`, `configure(key, value)` | the gateway's settings — its `url`, its `project` |
| `provider_config(name, key)`, `configure_provider(name, key, value)` | one provider's settings, answering or not |
| `token()` | the answering provider's `token` setting, if one is configured. The Mesh provider stores none: each of its requests carries a short-lived service token scoped to the project |
| `sources()` | the project's inputs and outputs, by stable id |
| `source_latest(source)`, `source_state(source)` | the newest reading of a source; the state behind it |
| `source_history(source, from_ms, to_ms, step_ms)` | readings over a range, Unix milliseconds as text; an empty step is raw readings |
| `action(source, state)` | switches an output `on` or `off`; answers whether the gateway did it |
| `nodes()` | the project's tree — the gateway, every board, module and device — as a JSON array |
| `device_states()` | `id:state` lines, for switch synchronisation |
| `follow(path)`, `transport()` | follows the live stream into a file; how it does: `bus`, `http` or `none` |
| `projects()`, `gateway()`, `register_client(...)`, `client_heartbeat(id)`, `publish(project, topic, payload)`, `telemetry_status()` | the rest of what a provider answers, for the keeper and Mesh's own pages |

## What a provider implements

Every function in `interface: functions:` of `module.yml`, with those
signatures. The calls are generated from the application's binding.
