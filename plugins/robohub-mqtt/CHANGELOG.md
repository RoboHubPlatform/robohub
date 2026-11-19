# Changelog

## [0.1.0] - 2026-11-13

First release: a Mosquitto broker the keeper runs as a user service of its own
on port 1884, beside any broker the system already has, with a broker user and
topic rules for every application that binds the bus and every device an admin
adds; applications reach it through robohub-provider-mqtt.

## [0.1.1] - 2026-11-19

The manifest did not validate (`rho module validate`: "plugin must declare `extends:`"), so the plugin could not be published. It plugs into no component of the toolchain, so it now declares itself the way the toolchain's plugin contract has a data-only integration plugin declare itself — `serves: [robohub]` and `integration.ecosystem: robohub` — rather than an `extends:` it would not honour. What the keeper reads (`integration.service`, `provides`, `provider`) is unchanged.
