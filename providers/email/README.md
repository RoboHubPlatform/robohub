# robohub-provider-email

The `alert` contract's `email` transport.

```rho
include "../../providers/email/src/provider.rho"
provider_email_send("local", "path=~/.rho/plugins/email-outbox.eml",
    "alerts@robohub.internal", "ops@robohub.internal", "Tank", "Water is high.")
```

`local` writes an `.eml` file; `smtp` uploads it with `smtp_host`,
`smtp_port`, `smtp_user`, `smtp_pass` and `smtp_security`.
