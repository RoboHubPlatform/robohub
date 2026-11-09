# Changelog

## [0.1.0] - 2026-11-04

The Mesh gateway provider, behind the gateway contract: projects, a project's
gateway, its sources, device states and a source's state.

## [0.2.0] - 2026-11-05

The provider behind this plugin now serves a source's telemetry: the newest
reading, a time-range series and the store's status. A caller may name a source
by its ID, its value or action URL, or a URL carrying `source=`, so an existing
widget or page does not have to be rewritten.

## [0.2.1] - 2026-11-06

Telemetry provider now serves latest, history, and status for mesh sources.
