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

## [0.3.0] - 2026-11-12

The language switcher reads its form through the form engine, which i18n now declares as a dependency, instead of a `form_value` the including application happened to define. The module builds on its own.

## [0.4.0] - 2026-11-13

Whole labels. An application that writes its labels in English carries a catalog
per language (`phrases.<locale>.txt`, English and the translation separated by a
tab), and `i18n_phrases(req, html, folder)` turns a page into the request's
language: a label is replaced only where it is a whole text between tags, a
placeholder or a title, a translation is never translated again, and what a page
receives later is translated in the browser from the same catalog. It was Mesh's;
every application has it now.

## [0.4.1] - 2026-11-13

The language switch returns only to a path on the same origin: a backslash (`/\\evil.example`, another host to a browser), a quote, an angle bracket, a space or a line break (another response header) sends it to `/` instead.

## [0.4.2] - 2026-11-14

Trimming comes from the toolchain (`str_trim`, rho 0.7.0) rather than this module's own copy.
