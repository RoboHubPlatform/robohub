# robohub-provider-webhook

An alert channel that posts each alert to an HTTP endpoint — a chat service's
incoming webhook, a home automation server, a script of your own. It implements
the `robohub.alert` interface (its `send`), and the application calls
`alert.raise(...)`, never the provider (see {ref}`robohub-alert/index`).

## Binding it

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
        content_type: application/json
```

## Settings

| Setting | Default | What it is |
|---|---|---|
| `url` | — | The endpoint; required, `http://` or `https://` |
| `content_type` | `application/x-www-form-urlencoded` | A type containing `json` posts `{"level","message","metadata"}` as JSON; anything else posts the same three fields as a form |
| `authorization` | — | When set, sent as the `Authorization` header exactly as written (`Bearer <token>`) |
| `severity_threshold` | everything | The lowest level posted: `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `enabled` | on | `"false"` stops the channel |

The body and the `Authorization` header are passed to `curl` through files (the
header through an owner-only one), never on a command line. An HTTP error is a
failure: `send` answers `1` only when the endpoint accepted the post.
