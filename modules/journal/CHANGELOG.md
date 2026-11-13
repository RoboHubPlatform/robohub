# Changelog

## [0.1.0] - 2026-11-13

What happened in an installation, in one table: time, level, kind, subject,
actor and message. `journal_write` and its `info`, `warning` and `error` forms
record an entry; warnings and errors are passed on as notifications and stay open
until resolved. A page filtered by level, kind and period, a JSON API, an open
count for a badge and pruning after three months.

## [0.1.1] - 2026-11-13

The clock is read from the process (`rho_now_s`, rho 0.6.0) instead of from `date` written to a file and read back, which a request and the background loop could truncate under each other: entries dated 1970 and modes that expired at once. Each entry's time is shown with the UTC offset it had (`rho_utc_offset_at`), so last winter's entries are not an hour off in summer.
