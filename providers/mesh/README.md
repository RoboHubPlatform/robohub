# robohub-provider-mesh

The `gateway` contract's `mesh` transport.

The provider owns the Mesh paths; the application calls the contract.

| Contract function | What the provider calls |
|---|---|
| `gateway_projects()` | `GET /mesh/api/projects` |
| `gateway_gateway()` | `GET /mesh/api/projects/{project}/gateway` |
| `gateway_sources()` | `GET /mesh/api/projects/{project}/sources?base={url}` |
| `gateway_device_states()` | the project's `GET /api/v1/devices` |
| `gateway_source_state(source)` | the source's `/value` path |
| `gateway_source_latest(source)` | the source's `/value` path, as a reading |
| `gateway_source_history(source, from, to, step)` | `GET /mesh/api/projects/{project}/telemetry/series` |
| `gateway_telemetry_status()` | `GET /mesh/api/projects/{project}/telemetry/status` |

The config is `url=...;project=...;token=...`; `url` is the Mesh application and
`project` is the project whose gateway and sources are used. The plugin
`mesh-gateway` supplies defaults and the application may override them in
`gateway.conf`.
