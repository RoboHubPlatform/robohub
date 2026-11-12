# Changelog

## [0.1.0] - 2026-11-08

First release. Adds locale negotiation from a cookie or `Accept-Language`, the
language switcher, and `i18n_vars` for Rho page helpers. Ships English and
Romanian shared catalogs.

## [0.2.0] - 2026-11-12

The module publishes its interface: it is imported as `robohub.i18n`, and exports
`i18n_t`, `i18n_vars`, `i18n_locale`, `i18n_switcher`. Everything else in it is its own, so an application that
imports it cannot reach its helpers, and they never collide with the
application's own names. Including it by name still works and is reported with
the import to use instead.
