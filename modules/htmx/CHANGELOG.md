# Changelog

## [0.1.0] - 2026-11-08

First release. Vendors HTMX 2.0.11 and htmx-ext-sse 2.2.4, serves them under
`/assets/`, and adds the fragment, redirect and event helpers a Rho host uses.

## [0.2.0] - 2026-11-12

The module publishes its interface: it is imported as `robohub.htmx`, and exports
`htmx_head`, `htmx_is_request`, `htmx_redirect`, `htmx_trigger`. Everything else in it is its own, so an application that
imports it cannot reach its helpers, and they never collide with the
application's own names. Including it by name still works and is reported with
the import to use instead.

## [0.2.1] - 2026-11-12

The module builds on its own: it compares strings with the language's own `str_eq` rather than a runtime function its includer had to declare.
