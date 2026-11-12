# Contracts

The interfaces an application calls. Each is a module an application declares
under `deps` and imports, and binds to the providers that implement it.

| Module | Import | Implemented by |
|--------|--------|----------------|
| `robohub-alert` (`contracts/alert/`) | `robohub.alert` | `providers/log`, `email`, `telegram`, `webhook` |
| `robohub-gateway` (`contracts/gateway/`) | `robohub.gateway` | `providers/mesh` |

An interface's `module.yml` declares the functions a provider implements
(`interface: functions:`), and an application binds the providers it wants
(`bind:`). The interface's code calls them through what the toolchain generates
from the binding, so neither it nor the application names a provider's
internals. An alert reaches every enabled channel bound; a gateway is one place,
so the first enabled provider bound answers.
