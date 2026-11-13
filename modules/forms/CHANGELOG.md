# Changelog

## [0.3.2] - 2026-11-13

The CSRF token is 256 random bits from the runtime, kept owner-only in the
application's workspace; a token an older release wrote — the workspace path and a
timestamp, which anyone could work out — is replaced the first time it is read. A
submit is compared with it without stopping at the first difference, and when no
random value can be had every submit is refused rather than a guessable token used.

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

## [0.3.0] - 2026-11-12

`FormField` is exported, so an application that imports `robohub.forms` names
the type of the fields it builds. A module's types are its own now, and one an
importer names has to be listed under `provides.exports`.

## [0.3.1] - 2026-11-12

The module builds on its own: it imports the template module whose `vars` it calls and declares the runtime functions it uses, rather than relying on the application that includes it to have declared them.
