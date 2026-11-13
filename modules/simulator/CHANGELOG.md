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

## [0.2.1] - 2026-11-13

The clock is read from the process (`rho_now_s`, rho 0.6.0) instead of from `date` written to a file and read back, which a request and the background loop could truncate under each other: entries dated 1970 and modes that expired at once. The time of day the `day` model follows likewise.

## [0.2.2] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0. A preset value that is not a number is 0, where its digits were picked out of it.
