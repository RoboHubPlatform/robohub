# Contracts

The interfaces an application calls. Each is a module an application declares
under `deps`.

| Module | Import | Implemented by |
|--------|--------|----------------|
| `robohub-alert` (`contracts/alert/`) | `robohub.alert` | `providers/log`, `email`, `telegram`, `webhook` |
| `robohub-contract-gateway` (`contracts/gateway/`) | included by name | `providers/mesh`, through the `mesh-gateway` plugin |

The alert interface is an interface in the toolchain's sense: its `module.yml`
declares the functions a provider implements (`interface: functions:`), and an
application binds the providers it wants (`bind:`). The interface's code calls
them through what the toolchain generates from the binding, so neither it nor
the application names a provider's internals.

The gateway contract still dispatches to the plugin an application names in its
`plugins:` block; it moves to the same form next.
