# Changelog

## [0.1.0] - 2026-11-13

The read-only REST API every RoboHub application offers in the same shape:
values derived from its presets (latest, avg, min, max, integral over a window
from the gateway's history, days since a journal event, exported readings),
values it publishes from its own code, each with 30 days of history, and its
journal. `/api/v1/values`, `/values/{id}`, `/values/{id}/history` in the
gateway's point shape, and `/api/v1/events`.
