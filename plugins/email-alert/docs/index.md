# email-alert

Sends an alert by e-mail. The alert builds the subject and body once and hands
them to the e-mail provider.

## Providers

`local` writes the rendered message to `~/.rho/plugins/email-outbox.eml`, which
is the default and needs no server. `smtp` uploads the same message with curl to
`smtp_host:smtp_port`; `smtp_security` is `ssl`, `starttls` or `none`, and
`smtp_user`/`smtp_pass` are optional.

## Templates

`subject_template` and `body_template` support `{level}`, `{message}`,
`{metadata}`, `{app}` and `{rule}`.

## Settings

| Key | Meaning |
|-----|---------|
| `provider` | `local` or `smtp` |
| `from_address` / `to_address` | envelope addresses |
| `smtp_host`, `smtp_port`, `smtp_user`, `smtp_pass`, `smtp_security` | SMTP transport |
| `severity_threshold` | lowest level it accepts |

A provider that speaks an HTTP API is another branch in the e-mail provider, not
a change to the alert or the rule that produced it.
