# Changelog

## [0.1.0] - 2026-11-02

The Telegram provider for the alert contract.

## [0.2.0] - 2026-11-12

A provider of the alert interface: the module lists `robohub.alert` under
`implements` and exports `send(level, message, metadata)`, which sends the alert to the chat in `chat_id`. Its
settings are declared under `provides.settings` and read with
`rho_bind_config`, from the binding of the application that uses it; the
`provider:` block and the `key=value;` configuration string are gone, and the
alert plugin that wrapped it was removed.

## [0.2.1] - 2026-11-13

An alert of several lines is one message again: the text goes to curl through a file (`--data-urlencode text@file`) instead of an argument, which a line break split in two, so every alert the rules sent with metadata failed. The bot token is read from a configuration file only this user can read, never from the command line; the token and chat id must be what Telegram issues; an HTTP error is a failure (`-f`).
