# robohub-provider-mesh

The provider of the gateway interface (`robohub.gateway`) that reaches Mesh:
an application such as aquarium or energy asks the interface for sources,
readings, history and the live feed, and this provider answers them from the
Mesh project the application is set to. It owns the Mesh paths; the application
calls the interface, never the provider (see
{ref}`robohub-gateway-contract/index`). It never talks to a gateway directly:
Mesh does that.

## Binding it

```yaml
deps:
  robohub:
    robohub-gateway: ">=1.1.0"
    robohub-provider-mesh: ">=0.5.0"

bind:
  robohub.gateway:
    providers: [robohub-provider-mesh]
    config:
      robohub-provider-mesh:
        url: "http://127.0.0.1:8478"
        project: "default"
        transport: auto
```

## Settings

| Setting | Default | What it is |
|---|---|---|
| `url` | — | Mesh's address, for an application started by hand. When the keeper starts the application, its `RHO_SERVICE_MESH_URL` wins |
| `project` | — | The Mesh project whose gateway and sources are used; without one the provider answers nothing |
| `transport` | `auto` | How `follow` gets the live feed: `auto` (the broker when the keeper gave the application one in `ROBOHUB_BUS_*`, Mesh's HTTP stream otherwise), `bus` (the broker or nothing) or `http` |
| `enabled` | on | `"false"` keeps it bound but not answering; the settings page's gateway tab sets it through `gateway.choose` |

`project` and `transport` are what the gateway tab of an application's settings
page changes (see {ref}`appshell/index`); they are written to the application's
`bind.conf`. No token is configured: every request carries a short-lived
service token for Mesh, scoped to the project (`mesh:<project>`), and a token is
only ever sent to Mesh's own address, never to a URL a person stored.

## What it calls

| Interface function | What the provider calls |
|---|---|
| `projects()` | `GET /mesh/api/projects` |
| `gateway()` | `GET /mesh/api/projects/{project}/gateway` |
| `sources()` | `GET /mesh/api/projects/{project}/sources?base={url}` |
| `nodes()` | `GET /mesh/api/projects/{project}/nodes` |
| `device_states()` | nothing: a device's state is a source's value, read by `source_state` |
| `source_state(source)` | the source's `/value` path |
| `source_latest(source)` | the source's `/value` path, as a reading |
| `source_history(source, from, to, step)` | `GET /mesh/api/projects/{project}/telemetry/series` |
| `telemetry_status()` | `GET /mesh/api/projects/{project}/telemetry/status` |
| `follow(path)` | the project's live feed, into `path`: the broker topic `mesh/{project}/telemetry` Mesh relays, or `GET /mesh/api/projects/{project}/telemetry/stream` |
| `transport()` | which of the two `follow` uses: `bus`, `http` or `none` |
| `action(source, state)` | `POST /mesh/api/projects/{project}/sources/{id}/action?state=on\|off` |
| `register_client`, `client_heartbeat`, `publish` | `POST /mesh/api/clients/...` |

Both transports write the same lines, so an application reads one file either
way. The broker needs the application to bind `robohub.bus` and to be allowed to
read `mesh/+/telemetry` (its manifest's `bus.subscribe`).

A source may be named by ID, by the value or action URL a widget stored, or by a
URL carrying `source=`. The provider extracts the same ID for all three.

Fetch failures are written to the host application log under the `gateway.mesh`
subject.
