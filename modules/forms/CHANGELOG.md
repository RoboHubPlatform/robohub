# Changelog

## [0.1.1] - 2026-11-08

Form fields support mobile input modes, `forms_open` takes the active locale and
translates the default submit label, and the form/CSRF/option/body markup is
carried in templates.

## [0.2.0] - 2026-11-12

The module publishes its interface: it is imported as `robohub.forms`, and exports
`forms_open`, `forms_parse`, `forms_read`, `forms_validate`, `forms_value`, `forms_payload`, `forms_csrf_field`, `forms_csrf_ok`, `forms_style`. Everything else in it is its own, so an application that
imports it cannot reach its helpers, and they never collide with the
application's own names. Including it by name still works and is reported with
the import to use instead.
