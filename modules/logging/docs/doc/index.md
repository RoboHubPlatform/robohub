# Logging

One logging policy for every application: the level, the format and the file
are chosen on the application's settings page and applied to everything the
program logs, its included modules among them.

## How an application uses it

Add `logging` to `deps` (it brings `settings` and `forms`, and the toolchain's
`rho-log` component) and include it. The module needs no host hooks.

- Call `log_config_apply(app)` once at startup. It reads the stored settings and
  hands them to the host's `logemit` port, which writes the records. Modules
  that log through `rho.log` inherit the same level, format and file.
- Show `log_settings_form(app, action, locale)` where the application keeps its
  settings, and save the posted form with `log_settings_save(app, body)`, which
  checks the CSRF field, validates and stores the values, and applies them at
  once. Applications that include `appshell` get both as its **Logging** tab.

## Settings

Kept in the application's settings store (see {ref}`settings/index`):

| Key | Default | What it is |
|---|---|---|
| `log.level` | `info` | `trace`, `debug`, `info`, `warn`, `error` or `fatal` |
| `log.format` | `text` | `text` for a terminal, `json` for a collector |
| `log.file` | see below | The application's own log file |
| `log.max_bytes` | `5242880` | The file is rotated before it grows past this size |
| `log.keep` | `5` | How many rotated files are kept |
| `log.stderr` | `1` | `1` also writes records to standard error, so journald sees them; `0` does not |

The default file is under the user's state directory, which is created when
needed:

```text
$XDG_STATE_HOME/robohub/<app>/app.log
~/.local/state/robohub/<app>/app.log      # when XDG_STATE_HOME is unset
```

`log_file_in_settings_file(path, app)` reads another application's log file from
its settings file; the keeper uses it to show each application's log.

## Environment

The host reads `RHO_LOG_LEVEL`, `RHO_LOG_FORMAT`, `RHO_LOG_FILE`,
`RHO_LOG_MAX_BYTES`, `RHO_LOG_KEEP` and `RHO_LOG_STDERR` when the program
starts. They are for tests and operators; `log_config_apply` sets the stored
settings on top of them.
