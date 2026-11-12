# Changelog

All notable changes to the alert contract are recorded here, one section per release.

## [0.1.1] - 2026-11-12

A plugin's kind and transport are read where the plugins declare them
(`module.plugin_kind`, `module.plugin_transport`), with a `plugin:` block still
accepted. Before, every plugin fell back to the log transport, so e-mail,
Telegram and webhook alerts were written to the log instead of sent. The plugin
list comes from the registry rather than placeholder rows, and nothing is written
into the plugins folder to make it.
