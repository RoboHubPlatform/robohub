# Changelog

## [0.1.0] - 2026-11-13

The read-only REST API every RoboHub application offers in the same shape:
values derived from its presets (latest, avg, min, max, integral over a window
from the gateway's history, days since a journal event, exported readings),
values it publishes from its own code, each with 30 days of history, and its
journal. `/api/v1/values`, `/values/{id}`, `/values/{id}/history` in the
gateway's point shape, and `/api/v1/events`.

## [0.1.1] - 2026-11-13

The clock is read from the process (`rho_now_s`, rho 0.6.0) instead of from `date` written to a file and read back, which a request and the background loop could truncate under each other: entries dated 1970 and modes that expired at once.

## [0.1.2] - 2026-11-13

A value's history returns the newest 5000 points of its window rather than the oldest, and each value to the nearest thousandth (0.007 was 0.006).

## [0.1.3] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0. A value is read with a decimal comma as well as a dot.

## [0.1.4] - 2026-11-14

`appapi_value` — a rule's host value and every dashboard card that shows one — looks the value up by its id, where it listed every value. `ignore_appapi` is `appapi_ignore`.
