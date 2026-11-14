# Changelog

## [0.1.0] - 2026-11-02

The generic HTTP provider for the alert contract.

## [0.2.0] - 2026-11-12

A provider of the alert interface: the module lists `robohub.alert` under
`implements` and exports `send(level, message, metadata)`, which posts the alert to `url`. Its
settings are declared under `provides.settings` and read with
`rho_bind_config`, from the binding of the application that uses it; the
`provider:` block and the `key=value;` configuration string are gone, and the
alert plugin that wrapped it was removed.

## [0.2.1] - 2026-11-13

An HTTP error is a failure, not a delivery (`-f`). A content type of application/json sends a JSON body. The URL must be http or https.

## [0.2.2] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0. A form value escapes every reserved byte; a space is `%20`.

## [0.2.3] - 2026-11-14

The authorization header reaches curl from an owner-only file rather than its command line, and a URL or header with a line break is refused.
