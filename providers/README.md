# Providers

Providers are modules, not plugins. Each one has an identity, a version, docs
and a changelog, and implements one contract's transport:

| Module | Contract | Transport | Functions |
|--------|----------|-----------|-----------|
| `robohub-provider-log` | alert | log | `provider_log_append(config, line)` |
| `robohub-provider-email` | alert | email | `provider_email_send(provider, config, from, to, subject, body)` |
| `robohub-provider-telegram` | alert | telegram | `provider_telegram_send(config, text)` |
| `robohub-provider-webhook` | alert | webhook | `provider_http_post(config, body)` |
| `robohub-provider-mesh` | gateway | mesh | `provider_mesh_*` behind the gateway contract |

The installed, selectable unit an application names is a **plugin**:
`alert-log`, `email-alert`, `telegram-notifier`, `webhook-alert` or
`mesh-gateway`. Each plugin names the provider it dispatches to in
`plugin.provider`, so the keeper can show the plugin a person installs and the
provider it carries.

`providers/registry.yml` is the installed provider set, read the same way
`plugins/registry.yml` is. It is what the keeper lists and what an install or
uninstall edits. It does not compete with the plugin registry: the provider
registry says what is installed, and the plugin registry says what an
application may enable. A provider is not selected directly by an application.

An application includes the provider it needs directly when it is not using the
manager:

```rho
include "../../providers/email/src/provider.rho"

let sent: u32 = provider_email_send(
    "smtp",
    "smtp_host=smtp.example.internal;smtp_port=587;smtp_user=bot;" +
    "smtp_pass=secret;smtp_security=starttls",
    "alerts@robohub.internal",
    "ops@robohub.internal",
    "[RoboHub] Water temperature",
    "The tank is above 28 C."
)
```

The config is the same `key=value;key=value` string a plugin receives. A
provider returns `1` when it accepted the message and `0` when it was incomplete
or the transport failed; the caller decides what that means.

`email` templates are rendered before the provider sees them, so a non-alert
caller passes the subject and body it wants directly. The alert dispatcher's
`subject_template` and `body_template` support `{level}`, `{message}`,
`{metadata}`, `{app}` and `{rule}`.
