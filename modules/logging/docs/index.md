# Logging

One logging policy for every application.

Each app has a **Logging** form in its Settings page: level (`trace` to
`fatal`), `text` or `json`, a file path, the size at which the file rotates,
how many rotated files to keep, and whether records also go to standard error.

The default file is under the user state directory:

```text
$XDG_STATE_HOME/robohub/<app>/app.log
~/.local/state/robohub/<app>/app.log
```

The application calls `log_config_apply(app)` at startup and after the form is
saved. The host's `logemit` port writes the records; included modules that call
`rho.log` inherit the same level, format and file. Standard error stays on by
default so journald also sees the service stream.

Environment overrides are for tests and operators: `RHO_LOG_LEVEL`,
`RHO_LOG_FORMAT`, `RHO_LOG_FILE`, `RHO_LOG_MAX_BYTES`, `RHO_LOG_KEEP` and
`RHO_LOG_STDERR`. Application settings call `log_configure` on top of them.
