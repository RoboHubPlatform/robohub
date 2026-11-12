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
