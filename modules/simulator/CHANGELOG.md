# Changelog

## [0.1.0] - 2026-11-13

One simulator for every RoboHub application, behind the gateway interface:
devices and sources from an application's presets, the models state, constant,
noise, when, day, thermal and integrator, actions on switches, a week of
history (raw or averaged into steps) and a live feed in Mesh's own stream
format. Settings choose it or the Mesh provider; nothing above the gateway can
tell which answers.

## [0.2.0] - 2026-11-13

`nodes()` (robohub-gateway 1.2.0): the simulated tree, a gateway, the boards a
device names in the presets (`board:`), and every device under its board. A `sum`
model adds and subtracts other sources (`of: a + b - c`, the signs between
spaces, so a dash inside a name such as `sim-ev.power` is part of it): a battery's
power from the site's surplus, a grid meter from what is left.
