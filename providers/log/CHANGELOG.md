# Changelog

## [0.1.0] - 2026-11-02

The local log provider for the alert contract.

## [0.1.1] - 2026-11-08

Alert logs append instead of reading and rewriting the whole file, and rotate at
1 MB with three retained files.

## [0.2.0] - 2026-11-12

A provider of the alert interface: the module lists `robohub.alert` under
`implements` and exports `send(level, message, metadata)`, which appends the alert to the file in `path`. Its
settings are declared under `provides.settings` and read with
`rho_bind_config`, from the binding of the application that uses it; the
`provider:` block and the `key=value;` configuration string are gone, and the
alert plugin that wrapped it was removed.

## [0.2.1] - 2026-11-13

The log is rotated at 1 MB again: the size stat answers ends in a line break, which made it read as 0, so the log was never rotated.

## [0.2.2] - 2026-11-14

Its data is kept where `app_workspace()` says (rho 0.8.0) — the application's workspace, else `~/.rho/apps/<app>` — so two applications started by hand no longer share this module's records. Needs rho 0.8.0.
