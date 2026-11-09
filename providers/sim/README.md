# robohub-provider-sim

The `gateway` contract's `sim` transport.

It presents an application's simulated sources in the same shape Mesh presents
real ones, so the widget source picker and the widget cards do not need a
separate simulation mode.

| Contract function | What the provider calls |
|---|---|
| `gateway_projects()` | an empty project list |
| `gateway_gateway()` | the configured `base` URL |
| `gateway_sources()` | `GET /api/energy/sim/gateway/sources` |
| `gateway_device_states()` | nothing; simulated sources are inputs |
| `gateway_source_state(source)` | nothing |
| `gateway_source_latest(source)` | `GET /api/energy/sim/gateway/latest?source=...` |
| `gateway_source_history(source, from, to, step)` | `GET /api/energy/sim/gateway/history?source=...` |
| `gateway_telemetry_status()` | `GET /api/energy/sim/gateway/status` |

The config is `transport=sim;base=<url>`. The energy application writes it while
its driver mode is `mock`; the application's settings then switch the same file
to `transport=mesh;url=...;project=...` for real-time mode.

Fetch failures are written to the host application log under the `sim-gateway` subject.
