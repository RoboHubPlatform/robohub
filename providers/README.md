# Providers

The transports the plugin system uses, and any application may use directly.
They are Rho functions rather than plugins, so the same e-mail path can carry an
alert, a report or a one-off message without going through a plugin registry.

| Provider | Function | What it does |
|----------|----------|--------------|
| `log` | `provider_log_append(config, line)` | appends a line to `path` |
| `email` | `provider_email_send(provider, config, from, to, subject, body)` | `local` writes to `~/.rho/plugins/email-outbox.eml`; `smtp` uploads with curl |
| `telegram` | `provider_telegram_send(config, text)` | posts to the Telegram bot API |
| `webhook` | `provider_http_post(config, body)` | posts a body to `url`, with `content_type` and optional `authorization` |

An application includes the provider it needs:

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

The config is the same `key=value;key=value` string an alert plugin receives. A
provider returns `1` when it accepted the message and `0` when it was incomplete
or the transport failed; the caller decides what that means. The alert manager
counts accepted sends and leaves delivery policy to the rule and the dispatcher.

`email` templates are rendered before the provider sees them, so a non-alert
caller passes the subject and body it wants directly. The alert dispatcher's
`subject_template` and `body_template` support `{level}`, `{message}`,
`{metadata}`, `{app}` and `{rule}`.
