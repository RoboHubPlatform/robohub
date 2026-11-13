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
