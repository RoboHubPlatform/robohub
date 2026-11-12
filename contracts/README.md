# Contracts

The stable interfaces an application calls, and the managers that dispatch them
to an installed plugin. Each is a module (`robohub-contract-<name>`, `main: manager.rho`) that an
application declares under `deps` and includes by name; it declares and includes
its providers the same way, so no path reaches outside a module's own folder.
`plugins/` holds the implementations.

| Contract | Manager | Providers |
|----------|---------|-----------|
| `alert` | `contracts/alert/manager.rho` | `providers/log`, `email`, `telegram`, `webhook` |
| `gateway` | `contracts/gateway/manager.rho` | `providers/mesh` |

An application names the plugin it wants in its `plugins:` block, and the
manager reads that block plus the provider's defaults. The application never
names a provider's URLs; the provider owns them.
