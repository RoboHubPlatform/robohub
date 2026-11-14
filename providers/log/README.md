# robohub-provider-log

An alert channel that appends each alert as a line to a file on the machine. It
implements the `robohub.alert` interface (its `send`), and the application calls
`alert.raise(...)`, never the provider (see {ref}`robohub-alert/index`). It needs
nothing outside the machine, which makes it the channel to bind first.

## Binding it

```yaml
deps:
  robohub:
    robohub-alert: ">=1.1.0"
    robohub-provider-log: ">=0.2.0"

bind:
  robohub.alert:
    providers: [robohub-provider-log]
    config:
      robohub-provider-log:
        path: "~/.rho/alerts.log"
```

## Settings

| Setting | Default | What it is |
|---|---|---|
| `path` | `~/.rho/alerts.log` | The file; a leading `~/` is the user's home. Its folder is created when needed |
| `severity_threshold` | everything | The lowest level written: `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `enabled` | on | `"false"` stops the channel |

Each line is `[<level>] <message> <metadata>`. The file is appended to rather
than rewritten, which is kinder to flash, and rotated once it passes 1 MB,
keeping three older files (`.1` to `.3`). `send` answers `1` when the line was
written.
