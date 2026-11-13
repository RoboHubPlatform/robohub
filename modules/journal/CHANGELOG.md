# Changelog

## [0.1.0] - 2026-11-13

What happened in an installation, in one table: time, level, kind, subject,
actor and message. `journal_write` and its `info`, `warning` and `error` forms
record an entry; warnings and errors are passed on as notifications and stay open
until resolved. A page filtered by level, kind and period, a JSON API, an open
count for a badge and pruning after three months.
