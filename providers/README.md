# Providers

A provider is a module that implements an interface: it lists the interface
under `implements`, exports the interface's functions with the interface's
signatures, and declares the settings it reads under `provides.settings`. Each
has an identity, a version, docs and a changelog.

| Module | Implements | Settings |
|--------|------------|----------|
| `robohub-provider-mesh` | `robohub.gateway` | `url`, `project`, `transport` |
| `robohub-provider-mqtt` | `robohub.bus` | `broker`, `user`, `password_file` |
| `robohub-provider-log` | `robohub.alert` | `path`, `severity_threshold` |
| `robohub-provider-email` | `robohub.alert` | `mode`, `to_address`, `from_address`, `app`, `subject_template`, `body_template`, `smtp_host`, `smtp_port`, `smtp_security`, `smtp_user`, `smtp_pass`, `severity_threshold` |
| `robohub-provider-telegram` | `robohub.alert` | `bot_token`, `chat_id`, `severity_threshold` |
| `robohub-provider-webhook` | `robohub.alert` | `url`, `content_type`, `authorization`, `severity_threshold` |

Every provider also accepts `enabled`: `"false"` keeps it bound but not
answering. The `simulator` module is a provider of `robohub.gateway` too, with
no settings of its own (see {ref}`simulator/index`).

## Binding a provider

An application declares the interface and the provider under `deps` and binds
the provider to the interface in its `bind:` block, with the provider's
settings under `config:`:

```yaml
deps:
  robohub:
    robohub-alert: ">=1.1.0"
    robohub-provider-webhook: ">=0.2.0"

bind:
  robohub.alert:
    providers: [robohub-provider-webhook]
    config:
      robohub-provider-webhook:
        url: "https://hooks.example.com/robohub"
```

The application calls the interface (`alert.raise(...)`), never the provider:
the toolchain generates the calls from the interface to the bound providers, and
only those are compiled in. A build refuses a binding to a module that does not
say it implements the interface, and a `config:` key the provider does not list
in `provides.settings`.

A provider reads its settings with `rho_bind_config(provider, key)`: the value
in the application's `bind.conf` (`<provider>.<key>=value` lines in its
workspace) when there is one, otherwise the `bind:` value. So a setting changed
on a running installation — the keeper's and the applications' settings pages
write `bind.conf` — wins over the default in the manifest. `bind.conf` is the
owner's only, because settings may be secrets.

How many bound providers answer depends on the interface: an alert reaches every
enabled channel; a gateway and a bus are one place each, so the first enabled
provider answers (see {ref}`robohub-alert/index`,
{ref}`robohub-gateway-contract/index`, {ref}`robohub-bus/index`).

## The installed set

`providers/registry.yml` is the installed provider set, read the same way
`plugins/registry.yml` is. It is what the keeper's Providers page lists and what
an install or uninstall edits; an application does not reach a provider through
it.
