# Changelog

## [0.1.0] - 2026-11-08

First release. Adds the host-owned key-value settings store used by applications
and their modules.

## [0.1.1] - 2026-11-12

The store also follows `RHO_APP_WORKSPACE`, the name the keeper gives an
application's workspace, so an application started with only that one keeps its
settings to itself instead of sharing the fallback store.

## [0.2.0] - 2026-11-12

The module publishes its interface: it is imported as `robohub.settings`, and exports
`settings_get`, `settings_set`, `settings_list`. Everything else in it is its own, so an application that
imports it cannot reach its helpers, and they never collide with the
application's own names. Including it by name still works and is reported with
the import to use instead.

## [0.2.1] - 2026-11-12

The module builds on its own: it declares the runtime functions it calls and no longer needs the including application's `ignore_u32`.

## [0.2.2] - 2026-11-14

Its data is kept where `app_workspace()` says (rho 0.8.0) — the application's workspace, else `~/.rho/apps/<app>` — so two applications started by hand no longer share this module's records. Needs rho 0.8.0.

## [0.2.3] - 2026-11-19

Security: a value with a line break was written as it was, so it added a key of its own to the store (`EUR\nlog.file=/somewhere`), and a key holding `=` read back as another key. `settings_set` now writes nothing for an empty key, a key holding `=`, or a key or value holding a line break or carriage return, and leaves the old value in place; `settings_valid(key, value)` says beforehand. Reads stay strict: only a line named exactly the key, the first one. The module has tests of its own (`tests/settings_test.rho`).

The directory it keeps its data in is made with `mkdir` given the path as one argument (`rho_exec_args`, one argument per line) rather than one string the runtime splits on spaces: a workspace path holding a space made stray directories from the words of the path, one of them relative to wherever the application runs, and on the C backend left the real directory unmade.
