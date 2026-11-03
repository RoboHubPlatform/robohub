# Changelog

## [0.1.3] - 2026-11-03

A switch card shows only the switch, larger and without the card border; its
title opens the widget settings. Pressing it from a dashboard stays there,
while the manager's Press button stays in the manager. A dashboard can always
offer **+ Add widget**.

## [0.1.2] - 2026-11-03

The widget device list resolves the gateway through a selected Mesh project
(`/mesh/api/projects/{project}/gateway`) instead of a gateway address stored by
Mesh.

## [0.1.1] - 2026-11-03

The widget editor can list devices from a connected Mesh/gateway and fill the
source with a chosen device's switch endpoint.

## [0.1.0] - 2026-11-02

Dashboard widgets with a configurable source: a number, a chart of recent
values, a button that calls a hook, and a switch that calls its hook with the new
state and shows that state. Values and definitions live in the host's main SQL
database; the manager and the API register on the host's router.
