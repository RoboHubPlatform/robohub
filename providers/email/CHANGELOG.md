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

## [0.2.1] - 2026-11-13

A header's value has its line breaks taken out, so a message or a rule name cannot add a header of its own; the SMTP password is read by curl from a file only this user can read, not from its command line; `{rule}` is the rule's name rather than the whole metadata; an SMTP error is a failure.

## [0.2.2] - 2026-11-14

Its data is kept where `app_workspace()` says (rho 0.8.0) — the application's workspace, else `~/.rho/apps/<app>` — so two applications started by hand no longer share this module's records. Needs rho 0.8.0.
