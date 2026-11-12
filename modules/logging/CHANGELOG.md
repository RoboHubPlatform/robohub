# Changelog

All notable changes to the logging module are recorded here, one section per release.

## [0.2.0] - 2026-11-12

The module publishes its interface: it is imported as `robohub.logging`, and exports
`log_config_apply`, `log_settings_form`, `log_settings_save`, `log_file_in_settings_file`. Everything else in it is its own, so an application that
imports it cannot reach its helpers, and they never collide with the
application's own names. Including it by name still works and is reported with
the import to use instead.

It imports robohub.settings and robohub.forms, which it uses and declares,
instead of relying on whoever includes it to have included them first.
