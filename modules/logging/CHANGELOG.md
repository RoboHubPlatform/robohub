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

## [0.2.1] - 2026-11-12

The module builds on its own: it declares the runtime functions it calls rather than relying on the application that includes it.

## [0.2.2] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0.

## [0.2.3] - 2026-11-14

`log_settings_field_defs` is exported: an application that draws the logging fields inside its own settings form uses it, and a build said it was not promised.
