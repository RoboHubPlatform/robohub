# alert-log

The local alert channel. It appends a line to a file, so an application can
enable it before any address or token exists.

## Settings

| Key | Meaning |
|-----|---------|
| `path` | file the line is appended to; defaults to `~/.rho/alerts.log` |
| `severity_threshold` | lowest level it accepts (`INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

The channel is enabled in an application's `plugins` list and reached through
the alert dispatcher. The line is:

```
[LEVEL] message metadata
```
