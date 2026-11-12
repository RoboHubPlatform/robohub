# Changelog

All notable changes to the alert interface are recorded here, one section per release.

## [0.1.1] - 2026-11-12

A plugin's kind and transport are read where the plugins declare them
(`module.plugin_kind`, `module.plugin_transport`), with a `plugin:` block still
accepted. Before, every plugin fell back to the log transport, so e-mail,
Telegram and webhook alerts were written to the log instead of sent. The plugin
list comes from the registry rather than placeholder rows, and nothing is written
into the plugins folder to make it.

## [1.0.0] - 2026-11-12

The alert contract is the alert interface, `robohub-alert` (import
`robohub.alert`), and the plugin manager is gone. An application declares the
interface and the providers it uses under `deps`, binds the providers in its
`module.yml`, and calls `alert.raise(level, message, metadata)`; the alert
reaches every bound channel that is enabled and whose `severity_threshold` it
meets. `alert.test`, `alert.providers`, `alert.enabled`, `alert.config` and
`alert.configure` are what a settings page uses, and a setting changed through
`configure` is kept in the application's `bind.conf`, so it holds on a running
installation without a rebuild. Only the bound providers are compiled in. The
alert rules moved to `src/rule.rho` with their tests, which the interface runs
itself (`rho test`), and string comparisons in them compare contents on C.
