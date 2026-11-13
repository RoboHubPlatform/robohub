# Changelog

## [0.1.0] - 2026-11-13

What happened in an installation, in one table: time, level, kind, subject,
actor and message. `journal_write` and its `info`, `warning` and `error` forms
record an entry; warnings and errors are passed on as notifications and stay open
until resolved. A page filtered by level, kind and period, a JSON API, an open
count for a badge and pruning after three months.

## [0.1.1] - 2026-11-13

The clock is read from the process (`rho_now_s`, rho 0.6.0) instead of from `date` written to a file and read back, which a request and the background loop could truncate under each other: entries dated 1970 and modes that expired at once. Each entry's time is shown with the UTC offset it had (`rho_utc_offset_at`), so last winter's entries are not an hour off in summer.

## [0.1.2] - 2026-11-13

The badge counts the open entries rather than the rows of a page of them, so it no longer stops at 500.

## [0.1.3] - 2026-11-14

Trimming, URL escapes, form fields and decimals come from the toolchain (rho 0.7.0: `str_trim`, `str_url_encode`/`str_url_decode`, `form_field`, `milli_*`) rather than this module's own copy, the same on both backends. Needs rho 0.7.0.
