# Changelog

## [0.1.0] - 2026-11-13

The rule engine RoboHub applications share. Conditions in a small fixed grammar
(comparisons of inventory readings, host values and literals; and, or, not,
brackets; the mode in force; a time window), actions on inventory items, alerts,
the journal and modes, and a state machine per rule with a pending window, a
clear condition and a cooldown. Modes run actions, suspend rules and end by
themselves. Rules and modes are seeded from an application's presets; a page and
a JSON API.

A rule whose action could not be done stays where it was and tries again, rather
than counting as fired; the problem is written to the journal once, not on every
evaluation.

## [0.1.1] - 2026-11-13

An ordering comparison (`<`, `<=`, `>`, `>=`) of a reading that is not a number is a problem, as a missing reading already was, not a false answer: `not t > 30` no longer holds — and acts — when the sensor says "unavailable".

## [0.1.2] - 2026-11-13

The clock is read from the process (`rho_now_s`, rho 0.6.0) instead of from `date` written to a file and read back, which a request and the background loop could truncate under each other: entries dated 1970 and modes that expired at once. The time of day for `time between` likewise (`rho_local_clock`).

## [0.1.3] - 2026-11-13

Durations read decimals and days: `1.5h` is 5400 seconds and `1d` 86400, where both were 0 and a rule's `for` or `cooldown` silently vanished. A mode is ended once: whoever clears it runs its end actions, so a tick and a person ending it together do not run them twice.

## [0.1.4] - 2026-11-13

A rule whose action failed keeps the failure until an action is done: while it waits out its minute, and while its condition comes and goes — a reading hovering at the threshold. The failure was cleared each time, so the action was tried at once whenever the condition held again and the failure written to the journal every few seconds. An item with no switch bound says so (`heater has no switch bound to a device`) rather than reading as a device that failed.

## [0.1.5] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0. A number in a condition may be written with a decimal comma; a lone `.` or `-` is no longer the number 0.
