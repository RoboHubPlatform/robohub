# robohub-provider-mesh

A provider of the gateway interface (`robohub-gateway`): the one that reaches
Mesh. The provider owns the Mesh paths; the application calls the interface.

| Interface function | What the provider calls |
|---|---|
| `projects()` | `GET /mesh/api/projects` |
| `gateway()` | `GET /mesh/api/projects/{project}/gateway` |
| `sources()` | `GET /mesh/api/projects/{project}/sources?base={url}` |
| `device_states()` | nothing: a device's state is a source's value, read by `source_state` |
| `source_state(source)` | the source's `/value` path |
| `source_latest(source)` | the source's `/value` path, as a reading |
| `source_history(source, from, to, step)` | `GET /mesh/api/projects/{project}/telemetry/series` |
| `telemetry_status()` | `GET /mesh/api/projects/{project}/telemetry/status` |
| `follow(path)` | the project's live feed, into `path`: the broker topic `mesh/{project}/telemetry` Mesh relays, or `GET /mesh/api/projects/{project}/telemetry/stream` |
| `transport()` | which of the two `follow` uses: `bus`, `http` or `none` |
| `action(source, state)` | `POST /mesh/api/projects/{project}/sources/{id}/action?state=on\|off` |
| `register_client`, `client_heartbeat`, `publish` | `POST /mesh/api/clients/...` |

Its settings come from the application's binding: `url` is the Mesh application
and `project` is the project whose gateway and sources are used. `transport` is
`auto` (the default: the broker when the keeper gave the application one in
`ROBOHUB_BUS_*`, Mesh's HTTP stream otherwise), `bus` (the broker or nothing) or
`http`. Both transports write the same lines, so an application reads one file
either way; the broker needs the application to bind `robohub.bus` and to be
allowed to read `mesh/+/telemetry` (its manifest's `bus.subscribe`). A supervisor's
`RHO_SERVICE_MESH_URL` wins over `url`. Every request carries a short-lived
service token for Mesh, scoped to the project; no token is stored.

A source may be named by ID, by the value or action URL a widget stored, or by a
URL carrying `source=`. The provider extracts the same ID for all three.

Fetch failures are written to the host application log under the `gateway.mesh`
subject.
