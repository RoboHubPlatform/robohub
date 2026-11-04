# robohub-provider-webhook

The `alert` contract's `webhook` transport.

```rho
include "../../providers/webhook/src/provider.rho"
provider_http_post("url=https://example.internal/hook;content_type=application/json",
    "{\"message\":\"Tank above 28 C\"}")
```

`url` is required; `content_type` defaults to `application/json` and
`authorization` is sent as a bearer header when present.
