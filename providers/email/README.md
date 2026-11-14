# robohub-provider-email

An alert channel that sends each alert as an e-mail: through an SMTP server, or
into a local outbox file so a machine with no mail server still shows what would
have gone out. It implements the `robohub.alert` interface (its `send`), and the
application calls `alert.raise(...)`, never the provider (see
{ref}`robohub-alert/index`).

## Binding it

```yaml
deps:
  robohub:
    robohub-alert: ">=1.1.0"
    robohub-provider-email: ">=0.2.0"

bind:
  robohub.alert:
    providers: [robohub-provider-email]
    config:
      robohub-provider-email:
        mode: smtp
        to_address: "ops@example.com"
        from_address: "robohub@example.com"
        smtp_host: "smtp.example.com"
        smtp_security: starttls
        severity_threshold: WARNING
```

Secrets such as `smtp_pass` belong in the application's `bind.conf` (written by
the settings page), not in the manifest.

## Settings

| Setting | Default | What it is |
|---|---|---|
| `mode` | `local` | `local` appends the message to `<workspace>/alerts/email-outbox.eml`; `smtp` sends it |
| `to_address` | — | The recipient; required — without it nothing is sent |
| `from_address` | `alerts@robohub.internal` | The sender |
| `app` | `RoboHub` | The name `{app}` stands for |
| `subject_template` | `[RoboHub {app}] {level}: {rule}` | The subject |
| `body_template` | `{message} ({app})` | The body |
| `smtp_host` | — | The SMTP server; required in `smtp` mode |
| `smtp_port` | `587` | Its port |
| `smtp_security` | none | `starttls` (or `tls`) requires STARTTLS; `ssl` (or `smtps`) connects over TLS |
| `smtp_user`, `smtp_pass` | — | The login, when the server needs one |
| `severity_threshold` | everything | The lowest level sent: `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `enabled` | on | `"false"` stops the channel |

The templates fill `{level}`, `{message}`, `{metadata}`, `{app}` and `{rule}`
(the rule the alert's metadata names, `{"rule":"too-warm"}`, or the metadata
itself). Line breaks are taken out of every header value, so a message cannot
add a header of its own.

`send` answers `1` when the message was written or accepted by the server, `0`
when a required setting is missing or the transfer failed. The mail is uploaded
with `curl`; the login is passed through an owner-only file, never on a command
line.
