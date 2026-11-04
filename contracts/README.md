# Contracts

The stable interfaces an application calls, and the managers that dispatch them
to an installed plugin. They are Rho sources included by the application, not
plugins themselves; `plugins/` holds the implementations.

| Contract | Manager | Providers |
|----------|---------|-----------|
| `alert` | `contracts/alert/manager.rho` | `providers/log`, `email`, `telegram`, `webhook` |
| `gateway` | `contracts/gateway/manager.rho` | `providers/mesh` |

An application names the plugin it wants in its `plugins:` block, and the
manager reads that block plus the provider's defaults. The application never
names a provider's URLs; the provider owns them.
