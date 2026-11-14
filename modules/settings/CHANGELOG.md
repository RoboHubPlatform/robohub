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
