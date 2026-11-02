# alert-dispatcher

The one alert plugin an application calls. It fans an alert out to the channels
named in `targets`; each channel keeps its own settings and threshold.

## Settings

| Key | Meaning |
|-----|---------|
| `targets` | comma-separated channel names, such as `alert-log,email-alert,telegram-notifier` |
| `severity_threshold` | lowest level the dispatcher accepts |

A target that is not installed, is disabled, or whose own threshold the level
does not reach is skipped. Without a dispatcher, the manager falls back to every
enabled alert plugin.
