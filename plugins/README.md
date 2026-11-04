# Plugins

Every directory in this folder is an installed plugin: it has a `module.yml`
with an identity, a `src/main.rho`, documentation, and a changelog, and it is
listed in `registry.yml`. A directory without those is not a plugin and does not
belong here.

The shared machinery is elsewhere:

- `contracts/alert/` — the alert manager and rule engine.
- `contracts/gateway/` — the gateway contract an application asks for a
  provider.
- `providers/` — the transports the contracts call, such as SMTP, a webhook,
  Telegram, or Mesh. Each has its own `module.yml` identity; the installed set
  is `providers/registry.yml`.

A contract is not a plugin: it is the stable interface an application calls. A
plugin is one implementation the contract dispatches to. This is what lets an
application change from one gateway provider to another by naming a different
plugin in its `plugins:` block, without learning either provider's API.
