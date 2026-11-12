# Changelog

## [0.1.0] - 2026-11-02

The local-outbox and SMTP provider for the alert contract.

## [0.2.0] - 2026-11-12

A provider of the alert interface: the module lists `robohub.alert` under
`implements` and exports `send(level, message, metadata)`, which sends the alert by SMTP or to the local outbox. Its
settings are declared under `provides.settings` and read with
`rho_bind_config`, from the binding of the application that uses it; the
`provider:` block and the `key=value;` configuration string are gone, and the
alert plugin that wrapped it was removed.
