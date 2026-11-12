# Providers

A provider is a module that implements an interface: it lists the interface
under `implements`, exports the interface's functions with the interface's
signatures, and declares the settings it reads under `provides.settings`. Each
has an identity, a version, docs and a changelog.

| Module | Implements | Settings |
|--------|------------|----------|
| `robohub-provider-log` | `robohub.alert` | `path`, `severity_threshold` |
| `robohub-provider-email` | `robohub.alert` | `mode`, `to_address`, `from_address`, `app`, `subject_template`, `body_template`, `smtp_*`, `severity_threshold` |
| `robohub-provider-telegram` | `robohub.alert` | `bot_token`, `chat_id`, `severity_threshold` |
| `robohub-provider-webhook` | `robohub.alert` | `url`, `content_type`, `authorization`, `severity_threshold` |
| `robohub-provider-mesh` | gateway | behind the gateway contract |

Every provider also accepts `enabled`.

An application uses a provider by declaring it under `deps` and binding it to
the interface:

```yaml
deps:
  robohub:
    robohub-alert: ">=1.0.0"
    robohub-provider-webhook: ">=0.2.0"

bind:
  robohub.alert:
    providers: [robohub-provider-webhook]
    config:
      robohub-provider-webhook:
        url: "https://hooks.example.internal/robohub"
```

The application calls the interface (`alert.raise(...)`), never the provider:
the toolchain generates the calls from the interface to the bound providers, and
only those are compiled in. A provider reads its settings with
`rho_bind_config(provider, key)`, so a setting changed on a running
installation (the application's `bind.conf`) wins over the default in `bind:`.

An alert provider's `send(level, message, metadata)` returns `1` when it
accepted the message and `0` when its settings are incomplete or the transport
failed. The e-mail provider's `subject_template` and `body_template` support
`{level}`, `{message}`, `{metadata}`, `{app}` and `{rule}`.

`providers/registry.yml` is the installed provider set, read the same way
`plugins/registry.yml` is. It is what the keeper's Providers page lists and what
an install or uninstall edits; an application does not reach a provider through
it.
