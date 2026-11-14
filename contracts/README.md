# Contracts

The interfaces an application calls. Each is a module an application declares
under `deps` and imports, and binds to the providers that implement it.

| Module | Import | Implemented by |
|--------|--------|----------------|
| `robohub-alert` (`contracts/alert/`) | `robohub.alert` | `robohub-provider-log`, `-email`, `-telegram`, `-webhook` (`providers/`) |
| `robohub-gateway` (`contracts/gateway/`) | `robohub.gateway` | `robohub-provider-mesh` (`providers/mesh`), and the `simulator` module |
| `robohub-bus` (`contracts/bus/`) | `robohub.bus` | `robohub-provider-mqtt` (`providers/mqtt`) |

An interface's `module.yml` declares the functions a provider implements
(`interface: functions:`), and an application binds the providers it wants
(`bind:`). The interface's code calls them through what the toolchain generates
from the binding, so neither it nor the application names a provider's
internals. An alert reaches every enabled channel bound; a gateway is one place,
so the first enabled provider bound answers; a bus is one broker, the same way.
A provider is enabled unless its `enabled` setting is `"false"`, and its
settings are its `bind:` values, overridden by the application's `bind.conf`.

On the documentation site the gateway interface's page is
`robohub-gateway-contract`, because the gateway repository has the name
`robohub-gateway`.

`registry.yml` is the installed set, in the shape of `providers/registry.yml`.

The wire protocol a board and a gateway speak is not an interface an application
calls; its schemas are in `protocol/`, one source copied into every consumer.
