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
| `follow(path)` | the project's telemetry stream, into `path` |
| `register_client`, `client_heartbeat`, `publish` | `POST /mesh/api/clients/...` |

Its settings come from the application's binding: `url` is the Mesh application
and `project` is the project whose gateway and sources are used. A supervisor's
`RHO_SERVICE_MESH_URL` wins over `url`. Every request carries a short-lived
service token for Mesh, scoped to the project; no token is stored.

A source may be named by ID, by the value or action URL a widget stored, or by a
URL carrying `source=`. The provider extracts the same ID for all three.

Fetch failures are written to the host application log under the `gateway.mesh`
subject.
